# Guia de apresentação — Base Aurora

Este documento explica, em linguagem de estudo, os pontos que o professor pediu:
**shaders, atributos de vértice, uniforms, transformações, renderização da cena
e a diferença entre sombreamento de superfície e sombra projetada**.

A ideia não é reconstruir o framework inteiro. É entender o caminho que os dados
percorrem em um quadro e saber apontar, no código, onde cada conceito aparece.

---

## 1. A frase que resume a apresentação

> **Os atributos descrevem cada vértice; os uniforms descrevem o contexto da
> renderização; os shaders são os programas que transformam esses dados em
> pixels; as matrizes posicionam objetos, câmera e luz; o sombreamento calcula
> a cor da superfície; e o shadow mapping calcula se a superfície está ou não
> visível para a luz.**

Se a dupla conseguir explicar essa frase com exemplos do projeto, a maior parte
da apresentação está resolvida.

---

## 2. O caminho de um quadro

Um quadro da cena passa por estas etapas:

```text
main.py
  └── Application.step(dt)
        ├── mission.update(time)          # posições/rotações dos modelos
        ├── scene.root.update_matrix()    # matrizes globais (pai × filho)
        └── renderer.render(scene, camera)
              ├── 1. passe de sombra      # câmera da luz → textura de profundidade
              ├── 2. céu procedural       # triângulo de tela cheia
              ├── 3. passe principal      # câmera normal → cor + profundidade
              └── 4. pós-processamento    # bloom + composição
```

No passe principal, para cada objeto:

```text
VBO com position/normal/uv
        ↓
vertex shader  (main.vert)
        ↓
rasterizador: monta triângulos e interpola os varyings
        ↓
fragment shader (main.frag)
        ↓
framebuffer: cor + profundidade
```

O renderizador faz isso duas vezes com câmeras diferentes:

- **câmera da luz**: só interessa a profundidade (shadow map);
- **câmera do jogador**: interessa a cor final.

Essa é a chave para entender o shadow mapping.

---

## 3. Shaders

### 3.1 O que é um shader

Um **shader** é um programa que roda na GPU. Os dois tipos usados no projeto são:

- **vertex shader**: executa uma vez por vértice. Recebe atributos e uniforms,
  transforma a posição para o espaço de recorte (`gl_Position`) e prepara dados
  para o fragment shader.
- **fragment shader**: executa uma vez por fragmento (candidato a pixel).
  Recebe valores interpolados do vertex shader e decide a cor final.

O projeto usa OpenGL 3.3 Core e GLSL 3.30 (`#version 330 core`).

### 3.2 Shaders efetivamente usados no projeto

| Programa | Arquivos | Para que serve |
|---|---|---|
| Passe principal | `shaders/main.vert` + `shaders/main.frag` | Transformar vértices, aplicar textura, iluminação Blinn-Phong, sombra e neblina. |
| Passe de profundidade | `shaders/depth.vert` + `shaders/depth.frag` | Renderizar a cena do ponto de vista da luz, gravando apenas profundidade. |
| Céu | `shaders/sky.vert` + `shaders/sky.frag` | Desenhar o céu procedural em tela cheia. |
| Bloom — brilho | `shaders/fullscreen.vert` + `shaders/bloom_bright.frag` | Extrair as partes claras da cena. |
| Bloom — blur | `shaders/fullscreen.vert` + `shaders/bloom_blur.frag` | Borrar horizontalmente e verticalmente. |
| Bloom — composição | `shaders/fullscreen.vert` + `shaders/composite.frag` | Somar a cena + bloom e aplicar vinheta. |

### 3.3 Vertex shader × fragment shader no passe principal

O `main.vert` faz três coisas:

```glsl
vec4 worldPos = u_model * vec4(a_position, 1.0);
v_normal = normalize(u_normalMatrix * a_normal);
v_uv = a_uv;

vec3 shadowWorld = worldPos.xyz + v_normal * 0.025;
v_lightSpacePos = u_lightVP * vec4(shadowWorld, 1.0);

gl_Position = u_projection * u_view * worldPos;
```

1. leva o vértice do espaço local para o mundo (`u_model`);
2. leva a normal para o mundo (`u_normalMatrix`);
3. leva o vértice para o espaço da luz (`u_lightVP`) e para o espaço de recorte
   da câmera (`u_projection * u_view`).

Os valores `v_worldPos`, `v_normal`, `v_uv` e `v_lightSpacePos` são **varyings**:
saem do vertex shader, são interpolados pelo rasterizador e entram no fragment
shader. Eles não são atributos nem uniforms.

O `main.frag` usa esses valores para calcular a cor:

```glsl
vec3 normal = normalize(v_normal);
vec3 lightDir = normalize(u_lightDirection);
vec3 viewDir = normalize(u_cameraPos - v_worldPos);
vec3 halfway = normalize(lightDir + viewDir);

float nDotL = max(dot(normal, lightDir), 0.0);
float specularAmount = pow(max(dot(normal, halfway), 0.0), max(u_shininess, 1.0));
```

### 3.4 Casos especiais: céu e fullscreen

O céu e o pós-processamento não desenham modelos 3D. Eles usam um único
triângulo que cobre a tela, gerado sem VBO:

```glsl
vec2 positions[3] = vec2[3](
    vec2(-1.0, -1.0),
    vec2( 3.0, -1.0),
    vec2(-1.0,  3.0)
);
```

O vertex shader usa `gl_VertexID` para escolher a posição de cada vértice. Por
isso, nesses programas **não há atributos de vértice**. O `sky.frag` usa
`u_invViewProj` para reconstruir a direção do raio de visão de cada pixel; os
shaders de bloom usam `v_uv` para amostrar texturas de tela.

### 3.5 O `depth.frag` vazio

No passe de profundidade, o fragment shader é praticamente vazio:

```glsl
void main()
{
    // O passe de profundidade não escreve cor: só o depth buffer importa.
}
```

Isso é intencional. O FBO da sombra não tem buffer de cor (`glDrawBuffer(GL_NONE)`),
apenas uma textura de profundidade. O importante é o valor de `gl_FragCoord.z`
que o OpenGL grava automaticamente no depth buffer.

---

## 4. Atributos de vértice

### 4.1 Definição

**Atributo de vértice** é um dado que acompanha cada vértice. No projeto, cada
vértice tem três atributos:

| Localização | Nome no shader | Tipo | O que representa |
|---|---|---|---|
| 0 | `a_position` | `vec3` | Posição do vértice no espaço local do objeto. |
| 1 | `a_normal` | `vec3` | Normal da superfície naquele vértice. |
| 2 | `a_uv` | `vec2` | Coordenada de textura. |

As localizações são fixadas antes de linkar o programa:

```python
# core/utils.py
glBindAttribLocation(program, 0, "a_position")
glBindAttribLocation(program, 1, "a_normal")
glBindAttribLocation(program, 2, "a_uv")
```

Isso garante que o mesmo VAO funcione com o passe principal e com o passe de
profundidade.

### 4.2 Como o Mesh cria o VAO/VBO

`core/mesh.py` percorre `geometry.attributes` e, para cada atributo:

1. gera um VBO;
2. envia os dados com `glBufferData`;
3. habilita o atributo com `glEnableVertexAttribArray`;
4. descreve o formato com `glVertexAttribPointer(location, size, GL_FLOAT, ...)`.

As geometrias são trianguladas e **não usam índices**: cada triângulo repete os
vértices. Isso simplifica o Mesh e o VAO, seguindo a abordagem didática do livro.

### 4.3 Por que normal e UV existem

- **Normal**: sem ela, o fragment shader não consegue calcular `dot(normal, luz)`
  nem o especular. A normal também é usada no deslocamento contra *shadow acne*.
- **UV**: sem ela, não é possível amostrar a textura de imagem com
  `texture(u_texture, v_uv)`.

### 4.4 O passe de profundidade usa só `position`

O `depth.vert` declara apenas:

```glsl
layout(location = 0) in vec3 a_position;
```

Ele não precisa de normal nem de UV, porque só quer saber onde o vértice está
para gravar profundidade. O VAO continua tendo os três atributos; o shader
simplesmente ignora os que não declara.

---

## 5. Uniforms

### 5.1 Definição

**Uniform** é um valor constante para toda a chamada de desenho (ou para todo o
programa, dependendo de quando é atualizado). Ele não muda por vértice nem por
fragmento. É o canal para enviar matrizes, cores, luzes, texturas e parâmetros
do material.

Diferença rápida:

| Conceito | Muda por... | Exemplo |
|---|---|---|
| Atributo | vértice | `a_position`, `a_normal`, `a_uv` |
| Uniform | draw call / programa | `u_model`, `u_view`, `u_lightColor` |
| Varying | sai do vertex e é interpolado até o fragment | `v_worldPos`, `v_normal`, `v_uv` |

### 5.2 Uniforms por quadro (câmera e luz)

Em `core/renderer.py`, antes de desenhar a cena, o renderizador envia:

| Uniform | Tipo | Papel |
|---|---|---|
| `u_view` | `mat4` | Matriz de visão da câmera. |
| `u_projection` | `mat4` | Projeção perspectiva. |
| `u_lightVP` | `mat4` | Visão × projeção ortográfica da luz. |
| `u_lightDirection` | `vec3` | Direção da superfície para a luz. |
| `u_lightColor` | `vec3` | Cor da luz direcional. |
| `u_ambientSky` / `u_ambientGround` | `vec3` | Ambiente hemisférico. |
| `u_cameraPos` | `vec3` | Posição da câmera para o especular e a neblina. |
| `u_fogColor`, `u_fogStart`, `u_fogEnd` | `vec3`, `float` | Neblina atmosférica. |
| `u_shadowEnabled` | `int` | Liga/desliga a sombra. |
| `u_shadowTexel` | `float` | Tamanho de um texel (`1/2048`). |
| `u_texture` / `u_shadowMap` | `sampler2D` | Unidades de textura 0 e 1. |

### 5.3 Uniforms por objeto e por material

Em `_draw_mesh`, para cada nó com malha, o renderizador envia:

| Uniform | Tipo | Papel |
|---|---|---|
| `u_model` | `mat4` | Matriz global do objeto (local × pais). |
| `u_normalMatrix` | `mat3` | Transposta da inversa da parte 3×3 de `u_model`. |
| `u_baseColor` | `vec3` | Cor base, multiplicada pela textura. |
| `u_specularColor` | `vec3` | Cor do especular. |
| `u_shininess` | `float` | Expoente do especular. |
| `u_ambientStrength` | `float` | Intensidade do ambiente. |
| `u_emissive` | `vec3` | Emissão (luzes, chamas, janelas). |
| `u_opacity` | `float` | Opacidade. |
| `u_unlit` | `int` | 1 = não iluminar (efeitos emissivos). |
| `u_useTexture` | `int` | 1 = amostrar a textura. |
| `u_receiveShadow` | `int` | 1 = o material recebe sombra. |

Esses valores vêm do `Material` de cada malha. É por isso que um mesmo shader
consegue desenhar areia, metal, vidro, chama e feixe com aparências diferentes.

### 5.4 Uniforms do passe de profundidade

| Uniform | Tipo | Papel |
|---|---|---|
| `u_lightVP` | `mat4` | Mesma matriz da luz usada no passe principal. |
| `u_model` | `mat4` | Matriz global do objeto que está sendo desenhado. |

O `depth.frag` não tem uniforms de cor, material ou textura.

### 5.5 Uniforms do céu e do pós-processamento

| Programa | Uniforms | Papel |
|---|---|---|
| `sky.frag` | `u_invViewProj`, `u_cameraPos`, `u_sunDir`, `u_zenithColor`, `u_horizonColor`, `u_sunColor` | Reconstruir a direção do raio e desenhar gradiente/sol/estrelas. |
| `bloom_bright.frag` | `u_scene`, `u_threshold` | Extrair luminância acima do limiar. |
| `bloom_blur.frag` | `u_image`, `u_direction` | Borrar em uma direção (horizontal ou vertical). |
| `composite.frag` | `u_scene`, `u_bloom`, `u_bloomStrength` | Somar cena + bloom e aplicar vinheta. |

### 5.6 Como o uniform chega ao shader

`core/shader.py` guarda o programa e o `location` de cada uniform. As funções
`set_mat4`, `set_mat3`, `set_vec3`, `set_float` e `set_int` chamam
`glUniform*`. O `location` é obtido com `glGetUniformLocation` e fica em cache.

Um detalhe importante: as matrizes NumPy estão na convenção matemática usual
(vetores coluna, `p' = M @ p`), mas o OpenGL espera column-major na memória.
Por isso o projeto envia com `GL_TRUE`:

```python
glUniformMatrix4fv(location, 1, GL_TRUE, data)
```

O `GL_TRUE` faz o OpenGL transpor o array durante o upload. Assim o código Python
fica legível (`M[linha, coluna]`) e o shader recebe a matriz correta.

---

## 6. Transformações

### 6.1 Matriz local e matriz global

Cada `Object3D` tem `translation`, `rotation` (Euler em graus) e `scale`.
A matriz local é:

```text
M_local = T · Rz · Ry · Rx · S
M_global = M_pai · M_local
```

Em `core/matrix.py`:

```python
def compose(position, rotation_degrees, scale_factors):
    return translation(*position) @ rotation(*rotation_degrees) @ scale(*scale_factors)
```

Em `core/object3d.py`:

```python
def update_matrix(self, parent_matrix=None):
    local = self.local_matrix()
    self.matrix = local if parent_matrix is None else parent_matrix @ local
    for child in self.children:
        child.update_matrix(self.matrix)
```

Isso é o que permite, por exemplo:

- o anel do disco girar em relação ao corpo do disco;
- o corpo do disco inclinar em relação à raiz;
- as aletas do foguete girarem em torno do corpo;
- os braços de fixação girarem 90° ao redor do foguete.

### 6.2 Do espaço local ao espaço de recorte

No `main.vert`:

```glsl
vec4 worldPos = u_model * vec4(a_position, 1.0);
gl_Position = u_projection * u_view * worldPos;
```

A ordem é:

```text
posição local
  --u_model--> mundo
  --u_view--> espaço da câmera
  --u_projection--> espaço de recorte
  --divisão por w--> NDC
  --viewport--> tela
```

O `u_model` muda por objeto; o `u_view` e o `u_projection` são os mesmos para
todos os objetos da cena naquele quadro.

### 6.3 Câmera em perspectiva

A `OrbitCamera` calcula a posição da câmera a partir de `yaw`, `pitch`,
`distance` e `target`. Depois:

- `matrix.look_at(eye, target, up)` monta a matriz de visão;
- `matrix.perspective(fov_y, aspect, near, far)` monta a projeção.

A projeção perspectiva faz os objetos distantes parecerem menores e cria o
efeito de profundidade. O aspecto é recalculado quando a janela é redimensionada.

### 6.4 Matriz normal

Se o objeto tem escala não uniforme (como as rochas e os elipsoides), usar
`u_model` diretamente na normal pode deixá-la não perpendicular à superfície.
A matriz normal corrige isso:

```python
def normal_matrix(model):
    return np.linalg.inv(model[:3, :3]).T
```

No shader:

```glsl
v_normal = normalize(u_normalMatrix * a_normal);
```

### 6.5 A luz também tem câmera

A luz direcional não tem posição, mas o shadow mapping precisa de uma câmera
virtual. `DirectionalLight.view_projection` cria:

```python
eye = center - self.direction * distance
view = look_at(eye, center, up)
projection = orthographic(-radius, radius, -radius, radius, 0.1, distance * 2.0)
return projection @ view
```

Como a luz é direcional, os raios são paralelos; por isso a projeção é
**ortográfica**, e não perspectiva.

---

## 7. Sombreamento de superfície

### 7.1 O que é

**Sombreamento** (shading) é o cálculo da cor de um ponto da superfície. Ele
responde à pergunta:

> “Dada a normal, o material, a textura, a luz e a câmera, qual é a cor deste
> fragmento?”

No projeto, o modelo é **Blinn-Phong** com ambiente hemisférico:

```text
ambiente  = albedo · mix(ambiente_chão, ambiente_céu, normal.y·0.5 + 0.5)
difusa    = albedo · cor_da_luz · max(dot(normal, luz), 0)
especular = cor_especular · cor_da_luz · pow(max(dot(normal, halfway), 0), shininess)
cor       = ambiente + (difusa + especular) · sombra + emissivo
```

No `main.frag`:

```glsl
vec3 hemisphere = mix(u_ambientGround, u_ambientSky, normal.y * 0.5 + 0.5);
vec3 ambient = albedo * hemisphere * u_ambientStrength;
vec3 diffuse = albedo * u_lightColor * nDotL;
vec3 specular = u_specularColor * u_lightColor * specularAmount * nDotL;

float shadow = shadowFactor(normal, lightDir);
color = ambient + (diffuse + specular) * shadow + u_emissive;
```

### 7.2 O que entra no sombreamento

- **Normal**: orientação da superfície.
- **Direção da luz**: `u_lightDirection`.
- **Direção da câmera**: `u_cameraPos - v_worldPos`, para o especular.
- **Material**: cor base, especular, brilho, ambiente.
- **Textura**: `texture(u_texture, v_uv)`.
- **Emissão**: somada no final, independente da luz.
- **Neblina**: mistura com a cor do horizonte pela distância.

### 7.3 O que o sombreamento não é

O sombreamento **não** é a sombra projetada. Mesmo com as sombras desligadas
(`F`), o shader continua calculando ambiente, difusa e especular. A sombra é um
fator de visibilidade que multiplica apenas a parte de luz direta.

---

## 8. Sombra projetada (shadow mapping)

### 8.1 O que é

**Sombra projetada** responde à pergunta:

> “Este ponto da superfície está escondido da luz por algum outro objeto?”

Ela não é uma textura pintada no chão. É o resultado de uma comparação de
profundidades feita com a cena vista do ponto de vista da luz.

### 8.2 As duas etapas

```text
ETAPA 1 — passe de profundidade
  câmera da luz
  → desenha a cena em um FBO
  → grava a menor profundidade de cada pixel
  → textura de profundidade 2048 × 2048

ETAPA 2 — passe principal
  câmera do jogador
  → para cada fragmento, calcula sua posição no espaço da luz
  → compara com a profundidade gravada
  → se estiver atrás, recebe sombra
```

### 8.3 O FBO da sombra

Em `core/shadow.py`:

- textura `GL_DEPTH_COMPONENT24` de 2048 × 2048;
- FBO com apenas `GL_DEPTH_ATTACHMENT`;
- `glDrawBuffer(GL_NONE)` e `glReadBuffer(GL_NONE)`;
- `GL_CLAMP_TO_BORDER` com borda `1.0`;
- filtro `GL_NEAREST`.

Não existe buffer de cor: o passe só quer profundidade.

### 8.4 O passe de profundidade

Em `core/renderer.py`:

```python
self.shadow.begin(scene.light)
glViewport(0, 0, self.shadow.size, self.shadow.size)
glClear(GL_DEPTH_BUFFER_BIT)

glEnable(GL_POLYGON_OFFSET_FILL)
glPolygonOffset(2.0, 4.0)

self.depth_program.use()
self.depth_program.set_mat4("u_lightVP", self.shadow.light_vp)
self._render_depth_tree(scene.root)
```

O `_render_depth_tree` só desenha objetos com `cast_shadow` e que não sejam
transparentes. Chamas, feixe e fumaça não entram.

O `glPolygonOffset` afasta ligeiramente os polígonos na profundidade para evitar
que a própria superfície se sombreie (shadow acne).

### 8.5 O passe principal

No `main.vert`, o vértice é levado para o espaço da luz:

```glsl
vec3 shadowWorld = worldPos.xyz + v_normal * 0.025;
v_lightSpacePos = u_lightVP * vec4(shadowWorld, 1.0);
```

O pequeno deslocamento na direção da normal é outro reforço contra shadow acne.

No `main.frag`:

```glsl
vec3 projected = v_lightSpacePos.xyz / v_lightSpacePos.w;
projected = projected * 0.5 + 0.5;

float bias = max(0.0018 * (1.0 - dot(normal, lightDir)), 0.0005);
float visibility = 0.0;

for (int x = -1; x <= 1; ++x) {
    for (int y = -1; y <= 1; ++y) {
        vec2 offset = vec2(float(x), float(y)) * u_shadowTexel;
        float closest = texture(u_shadowMap, projected.xy + offset).r;
        visibility += (projected.z - bias > closest) ? 0.0 : 1.0;
    }
}
return visibility / 9.0;
```

Passo a passo:

1. **divisão por `w`**: leva de espaço de recorte para NDC;
2. **`* 0.5 + 0.5`**: leva de `[-1, 1]` para `[0, 1]`, que é o intervalo da
   textura;
3. **comparação**: se a profundidade do fragmento (`projected.z`) for maior que
   a menor profundidade gravada (`closest`), há um objeto na frente → sombra;
4. **PCF 3 × 3**: repete a comparação nos 9 texels vizinhos e faz a média. Isso
   suaviza a borda da sombra;
5. **bias**: evita que o próprio fragmento se considere sombreado por causa de
   erro de precisão.

### 8.6 Por que a sombra se move

O shadow map é **regenerado a cada quadro**. As matrizes dos objetos são
atualizadas pela missão, o passe de profundidade redesenha a cena do ponto de
vista da luz e a textura de profundidade muda. Por isso a sombra do foguete e do
disco acompanha o movimento.

### 8.7 Por que a sombra não apaga o ambiente

A linha:

```glsl
color = ambient + (diffuse + specular) * shadow + u_emissive;
```

mostra que a sombra multiplica apenas **difusa + especular**. O ambiente e a
emissão continuam. É por isso que uma região sombreada não fica totalmente
preta.

---

## 9. Sombreamento × sombra: a diferença em uma tabela

| Pergunta | Sombreamento de superfície | Sombra projetada |
|---|---|---|
| O que calcula? | A cor da superfície. | Se o ponto está oculto da luz. |
| Onde acontece? | `main.frag`, por fragmento. | Passe de profundidade + comparação no `main.frag`. |
| Depende de quê? | Normal, material, textura, luz, câmera. | Profundidade da cena vista da luz. |
| É calculado por objeto? | Sim, com os uniforms do material. | Não: é uma relação entre objetos. |
| Some quando `F` é desligado? | Não. O shading continua. | Sim. O fator de sombra vira 1.0. |
| Pode existir sem o outro? | Sim: dá para sombrear sem projetar sombra. | Não faz sentido sozinho: a sombra modula o shading. |
| Exemplo no projeto | Difusa + especular do foguete. | Sombra do foguete no chão/plataforma. |

Uma frase para a apresentação:

> **O sombreamento decide a cor da superfície; a sombra decide quanto da luz
> direta chega até ela. A sombra não substitui o sombreamento — ela o modula.**

---

## 10. Céu e pós-processamento (explicação curta)

### 10.1 Céu procedural

O `sky.vert` desenha um triângulo que cobre a tela. O `sky.frag` usa
`u_invViewProj` para transformar a posição de tela em uma direção no mundo:

```glsl
vec4 world = u_invViewProj * vec4(v_ndc, 1.0, 1.0);
vec3 direction = normalize(world.xyz / world.w - u_cameraPos);
```

Com a direção, ele desenha:

- gradiente entre `u_horizonColor` e `u_zenithColor`;
- disco e halo do sol usando `dot(direction, u_sunDir)`;
- estrelas com uma função hash;
- dithering para reduzir banding.

### 10.2 Bloom

O pipeline é:

```text
cena → FBO da cena
     → bloom_bright (extrai brilho)
     → blur horizontal
     → blur vertical
     → composite (cena + bloom + vinheta)
```

O bloom é um efeito de tela, não de geometria. Por isso os shaders usam
`fullscreen.vert` e texturas (`u_scene`, `u_image`, `u_bloom`), sem atributos de
vértice 3D.

---

## 11. Roteiro de 10 minutos para a dupla

### Pessoa A — pipeline, shaders, atributos e uniforms (5 min)

1. **Abrir com a frase-resumo** da seção 1.
2. Mostrar o caminho de um quadro (seção 2) e dizer que o renderizador faz dois
   passes: luz e câmera.
3. Explicar o que é shader e listar os programas do projeto (seção 3.2).
4. Mostrar `main.vert` e explicar `u_model`, `u_view`, `u_projection`,
   `u_lightVP` e `u_normalMatrix`.
5. Mostrar os três atributos (`a_position`, `a_normal`, `a_uv`) e o `Mesh`
   criando o VAO/VBO. Destacar que o `depth.vert` usa só `a_position`.
6. Explicar a diferença atributo × uniform × varying.
7. Mostrar `Object3D.update_matrix` e a composição `M_pai · M_local`.

### Pessoa B — sombreamento, sombra e demonstração (5 min)

1. Explicar o Blinn-Phong do `main.frag` (ambiente, difusa, especular,
   emissiva).
2. Explicar o shadow mapping em duas etapas (seção 8.2).
3. Mostrar o FBO de profundidade e o `depth.vert`/`depth.frag`.
4. Mostrar a comparação de profundidade com PCF 3 × 3 e o bias.
5. Enfatizar a diferença sombreamento × sombra (tabela da seção 9).
6. Demonstração ao vivo:
   - pausar em `t ≈ 8 s` para mostrar o feixe;
   - em `t ≈ 20 s`, apertar `F` para comparar sombra ligada/desligada;
   - apertar `B` para comparar bloom;
   - orbitar a câmera com as setas e dar zoom com `W`/`S`;
   - redimensionar a janela para mostrar a atualização do aspecto.
7. Fechar com a frase: “a sombra não é uma textura no chão; é uma comparação de
   profundidades feita do ponto de vista da luz”.

---

## 12. Demonstração: o que mostrar e o que dizer

| Ação | O que dizer |
|---|---|
| `python main.py` | “A cena roda em OpenGL 3.3 Core; o loop é `main.py`.” |
| Pausar em `t ≈ 8 s` | “O disco está orbitando e o feixe é um cone transparente aditivo.” |
| Em `t ≈ 20 s`, apertar `F` | “Agora as sombras somem; o shading continua. A sombra é um fator à parte.” |
| Apertar `B` | “O bloom é pós-processamento: brilho, blur e composição.” |
| Setas e `W`/`S` | “A câmera é perspectiva e orbital; o `u_view`/`u_projection` são atualizados por quadro.” |
| Redimensionar | “O aspecto muda e a projeção é recalculada.” |
| Voltar as sombras | “O shadow map é regenerado a cada quadro; por isso a sombra acompanha o foguete.” |

---

## 13. Perguntas prováveis do professor

### 1. O que é um shader?

É um programa que roda na GPU. O vertex shader processa vértices e o fragment
shader processa fragmentos. No projeto, `main.vert` transforma posições e
`main.frag` calcula a cor.

### 2. Qual a diferença entre atributo, uniform e varying?

- **Atributo**: dado por vértice, vem do VBO.
- **Uniform**: valor constante para a chamada de desenho, vem da CPU.
- **Varying**: saída do vertex shader que é interpolada e chega ao fragment
  shader.

### 3. Quais atributos o projeto usa?

`a_position` (`vec3`), `a_normal` (`vec3`) e `a_uv` (`vec2`), nas localizações
0, 1 e 2. O passe de profundidade usa apenas `a_position`.

### 4. Por que o `depth.frag` é vazio?

Porque o passe de profundidade não escreve cor. Só o depth buffer importa. O FBO
da sombra nem tem anexo de cor.

### 5. Por que a matriz normal não é o `u_model`?

Porque escala não uniforme distorce as normais. A matriz normal é
`transpose(inverse(model[:3,:3]))`, que mantém a normal perpendicular à
superfície.

### 6. Por que usar `GL_TRUE` no `glUniformMatrix4fv`?

Porque as matrizes NumPy estão em row-major matemático e o OpenGL espera
column-major. O `GL_TRUE` transposta no upload.

### 7. Como a câmera é montada?

`OrbitCamera` calcula `eye` a partir de yaw/pitch/distância; `look_at` monta a
view; `perspective` monta a projeção com FOV, aspecto, near e far.

### 8. O que é o `u_lightVP`?

É a matriz que leva um ponto do mundo para o espaço da luz:
`orthographic @ look_at`. Ela é usada no passe de profundidade e no passe
principal para comparar profundidades.

### 9. Por que a projeção da luz é ortográfica?

Porque a luz é direcional: os raios são paralelos, não saem de um ponto. Uma
projeção ortográfica representa isso corretamente.

### 10. Como funciona o shadow mapping?

Renderiza a cena do ponto de vista da luz gravando profundidade. No passe
principal, compara a profundidade do fragmento com a menor profundidade
armazenada. Se o fragmento estiver atrás, ele está na sombra.

### 11. O que é PCF?

Percentage Closer Filtering. Em vez de uma comparação, faz 9 comparações em uma
vizinhança 3 × 3 e tira a média. Isso suaviza a borda da sombra.

### 12. Para que serve o bias?

Para evitar *shadow acne*: o próprio fragmento pode ser considerado atrás de si
mesmo por erro de precisão. O bias dá uma pequena margem.

### 13. Por que a sombra não deixa tudo preto?

Porque a sombra multiplica apenas difusa + especular. O ambiente e a emissão
continuam.

### 14. Qual a diferença entre sombreamento e sombra projetada?

Sombreamento é a cor da superfície (normal, material, luz, câmera). Sombra
projetada é a visibilidade da superfície em relação à luz (comparação de
profundidades). A sombra modula o sombreamento.

### 15. O que acontece quando aperto `F`?

`Renderer.shadows_enabled` vira `False`; o passe de profundidade não é
executado e `u_shadowEnabled` vai como 0. O `shadowFactor` retorna 1.0, então
toda a luz direta chega à superfície.

### 16. Por que chamas, feixe e fumaça não projetam sombra?

Porque são transparentes e usam `cast_shadow = False`. O passe de profundidade
só desenha objetos opacos com `cast_shadow`; misturar transparência nesse passe
daria sombras erradas.

### 17. O que é o bloom?

É um efeito de pós-processamento: extrai as regiões claras, borra e soma de volta
na cena. Ele não altera a geometria nem a iluminação; é um efeito de tela.

### 18. O céu usa atributos de vértice?

Não. O céu e o pós-processamento usam um triângulo de tela cheia gerado com
`gl_VertexID`, sem VBO. O `sky.frag` reconstrói a direção do raio com
`u_invViewProj`.

### 19. Por que a animação não depende do FPS?

Porque `mission.update(time)` calcula tudo a partir do tempo absoluto. O `dt` só
avança `self.time`; a posição não é incrementada “por quadro”. A câmera também
usa `dt`, mas a coreografia é função do tempo.

### 20. O trabalho simula física ou colisão?

Não. A coreografia é uma sequência de interpolações suaves (`smoothstep`,
`smootherstep`, `phase`). Não há motor físico nem detecção de colisão, o que está
de acordo com o enunciado.

---

## 14. Glossário rápido

| Termo | Significado |
|---|---|
| **Shader** | Programa executado na GPU. |
| **Vertex shader** | Processa vértices; calcula `gl_Position`. |
| **Fragment shader** | Processa fragmentos; calcula a cor. |
| **Atributo** | Dado por vértice (posição, normal, UV). |
| **Uniform** | Valor global da chamada de desenho (matriz, cor, luz). |
| **Varying** | Valor interpolado entre vertex e fragment shader. |
| **VAO** | Vertex Array Object: guarda a configuração dos atributos. |
| **VBO** | Vertex Buffer Object: guarda os dados dos vértices. |
| **FBO** | Framebuffer Object: destino de renderização fora da tela. |
| **Shadow map** | Textura de profundidade vista da luz. |
| **PCF** | Filtro que suaviza a borda da sombra com várias comparações. |
| **Bias** | Margem para evitar shadow acne. |
| **Blinn-Phong** | Modelo de iluminação com ambiente, difusa e especular. |
| **Matriz normal** | `transpose(inverse(model[:3,:3]))`. |
| **NDC** | Normalized Device Coordinates, intervalo `[-1, 1]`. |
| **Bloom** | Efeito de brilho por pós-processamento. |

---

## 15. Checklist antes de apresentar

- [ ] Rodar `python main.py` e confirmar que a janela abre.
- [ ] Testar `Espaço` (pausa), `F` (sombras), `B` (bloom), `R` (reinício),
      `C` (câmera) e as setas/W/S.
- [ ] Deixar o terminal pronto para mostrar `python main.py --screenshot ...`.
- [ ] Abrir `shaders/main.vert`, `shaders/main.frag`, `core/mesh.py`,
      `core/object3d.py` e `core/shadow.py` em abas separadas.
- [ ] Ter as imagens `screenshots/sombras_on.png` e `screenshots/sombras_off.png`
      à mão para a comparação.
- [ ] Treinar a frase final: **“shading calcula a cor; shadow mapping calcula a
      visibilidade da luz”**.
