# Base Aurora — Disco Voador + Foguete

Trabalho prático de Computação Gráfica — 2026/02

**Tema:** Disco voador + Foguete

**Integrantes:**
- Marco Antônio — 231-001036
- Pedro Souza — 231-002821

## 1. Visão geral

**Base Aurora** é uma cena 3D interativa em tempo real, escrita em **Python** com
**Pygame** (janela e entrada) e **PyOpenGL** (OpenGL 3.3 Core). A cena
representa uma base de testes no deserto ao entardecer, onde um disco voador se
aproxima, inspeciona um foguete com um feixe de varredura, sinaliza autorização
e acompanha um pequeno salto de teste do foguete.

O projeto foi construído sobre um framework reduzido, inspirado no livro
*Developing Graphics Frameworks with Python and OpenGL* (Stemkoski & Pascale).
Todos os modelos são formados por primitivas geométricas simples: esferas,
elipsoides, cilindros, cones, toros, caixas e prismas extrudados. Não há modelos
3D, imagens ou texturas de terceiros — todas as texturas são geradas
proceduralmente pelo script `tools/generate_textures.py`.

### Imagens da cena

| Aproximação | Varredura |
|---|---|
| ![Aproximação](screenshots/01_aproximacao.png) | ![Varredura](screenshots/02_varredura.png) |

| Sinal verde | Salto de teste |
|---|---|
| ![Sinal](screenshots/03_sinal.png) | ![Salto](screenshots/04_salto.png) |

| Pouso | Retorno |
|---|---|
| ![Pouso](screenshots/05_pouso.png) | ![Retorno](screenshots/06_retorno.png) |

Comparação de sombra projetada (tecla `F`, no instante `t = 20 s`, com o
foguete em subida):

| Sombras ligadas | Sombras desligadas |
|---|---|
| ![Sombras ligadas](screenshots/sombras_on.png) | ![Sombras desligadas](screenshots/sombras_off.png) |

---

## 2. Instalação e execução

### Requisitos

- Python 3.10 ou superior (testado com Python 3.14.7 no Windows).
- Placa de vídeo/driver com suporte a **OpenGL 3.3 Core**.
- Uma janela real: o contexto OpenGL não funciona com o driver SDL `dummy`.

### Passos

No Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python tools/generate_textures.py   # opcional: as texturas já estão incluídas
python main.py
```

No Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python tools/generate_textures.py
python main.py
```

> `PyOpenGL_accelerate` é opcional e está comentado em `requirements.txt`. O
> projeto funciona somente com `PyOpenGL`.

### Execução sem interação (para capturas de tela)

```powershell
python main.py --screenshot screenshots/cena.png --time 21
```

| Opção | Descrição |
|---|---|
| `--width` / `--height` | Resolução inicial da janela (padrão 1600 × 900). |
| `--screenshot CAMINHO` | Renderiza um quadro, salva em PNG e encerra. |
| `--time SEGUNDOS` | Instante da animação usado no screenshot. |
| `--no-shadows` | Desliga o shadow mapping (comparação). |
| `--no-bloom` | Desliga o bloom (comparação). |

Exemplos:

```powershell
python main.py --screenshot screenshots/sem_sombras.png --time 21 --no-shadows
python main.py --screenshot screenshots/sem_bloom.png --time 21 --no-bloom
```

---

## 3. Controles

| Tecla | Ação |
|---|---|
| `←` / `→` | Orbita a câmera (yaw). |
| `↑` / `↓` | Inclina a câmera (pitch). |
| `W` / `+` | Aproxima a câmera (zoom in). |
| `S` / `-` | Afasta a câmera (zoom out). |
| `Espaço` | Pausa/retoma a animação **sem parar a renderização**. |
| `R` | Reinicia a linha do tempo em `t = 0`. |
| `C` | Restaura a câmera inicial. |
| `F` | Liga/desliga as sombras projetadas. |
| `B` | Liga/desliga o bloom. |
| `Esc` | Encerra o programa. |

A câmera continua respondendo aos controles enquanto a animação está pausada.
O título da janela mostra o estado (`ANIMANDO`/`PAUSADO`), sombras, bloom, FPS
e o tempo atual.

---

## 4. A cena e a animação (coreografia)

A cena é uma base de lançamento no deserto, com plataforma listrada, quatro
braços de fixação, torre de serviço, bunker de controle, rochas, cactos e
mesetas ao fundo. O disco voador e o foguete são os dois elementos principais.

A interação é uma **coreografia de 32 segundos**, calculada a partir do tempo
absoluto `time` (não por quadro, portanto independente do FPS):

| Intervalo (s) | Etapa |
|---|---|
| 0,0 – 6,0 | O disco voador se aproxima e entra em órbita. |
| 6,0 – 14,0 | Inspeção orbital; entre 6,8 s e 13,2 s o feixe de varredura atinge o foguete. |
| 14,0 – 16,5 | O disco se posiciona, pisca em verde e os quatro braços se abrem. |
| 16,5 – 17,5 | Ignição do motor, com vibração e fumaça. |
| 17,5 – 21,5 | Subida do foguete; o disco acompanha o movimento. |
| 21,5 – 23,0 | Foguete pairando no alto; disco observando. |
| 23,0 – 26,0 | Descida e pouso do foguete. |
| 26,3 – 27,5 | Fechamento dos braços de fixação. |
| 27,5 – 30,5 | Retorno do disco à posição inicial. |
| 30,5 – 32,0 | Pequena pausa e reinício do ciclo. |

A interação exigida pelo trabalho está na **dependência entre os dois modelos**:
o disco **escaneia** o foguete, **sinaliza** e **abre os braços**; somente
depois o foguete **ignita** e salta. Durante o voo, o disco **segue** o foguete,
e ao final ambos retornam ao estado inicial.

Toda a animação é controlada por `scene/mission.py` (`Mission.update(time)`),
que usa interpolações suaves (`smoothstep`, `smootherstep`, `phase`).

---

## 5. Funcionamento interno — o caminho de um quadro

Esta seção explica, passo a passo, como os dados percorrem o pipeline desde o
código Python até os pixels na tela. É o resumo do conteúdo que antes estava
no `APRESENTACAO.md`.

### 5.1 Fluxo de execução

Cada quadro segue este caminho:

```text
main.py
  └── Application.step(dt)
        ├── mission.update(time)          # posições/rotações dos modelos
        ├── scene.root.update_matrix()    # matrizes globais (pai × filho)
        └── renderer.render(scene, camera)
              ├── 1. passe de sombra      # câmera da luz → textura de profundidade (shadow map)
              ├── 2. céu procedural       # triângulo de tela cheia
              ├── 3. passe principal      # câmera normal → cor + profundidade
              └── 4. pós-processamento    # bloom (brilho, blur, composição)
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

O renderizador usa **duas câmeras diferentes**:

- **Câmera da luz**: só interessa a profundidade (gera o shadow map).
- **Câmera do jogador**: interessa a cor final.

Essa é a chave para entender o shadow mapping.

### 5.2 Shaders

Um **shader** é um programa que roda na GPU. O projeto usa OpenGL 3.3 Core e
GLSL 3.30 (`#version 330 core`).

| Tipo | O que faz | Quando roda |
|---|---|---|
| **Vertex shader** | Transforma a posição de cada vértice para o espaço de recorte (`gl_Position`) e prepara dados para o fragment shader. | Uma vez por vértice. |
| **Fragment shader** | Decide a cor final de cada fragmento (candidato a pixel) a partir de valores interpolados. | Uma vez por fragmento. |

#### Programas de shader usados no projeto

| Programa | Arquivos | Para que serve |
|---|---|---|
| Passe principal | `shaders/main.vert` + `shaders/main.frag` | Transformação, textura, iluminação Blinn-Phong, sombra e neblina. |
| Passe de profundidade | `shaders/depth.vert` + `shaders/depth.frag` | Renderiza a cena do ponto de vista da luz, gravando apenas profundidade. |
| Céu | `shaders/sky.vert` + `shaders/sky.frag` | Céu procedural em tela cheia. |
| Bloom — brilho | `shaders/fullscreen.vert` + `shaders/bloom_bright.frag` | Extrai as regiões claras da cena. |
| Bloom — blur | `shaders/fullscreen.vert` + `shaders/bloom_blur.frag` | Borra horizontalmente e verticalmente. |
| Bloom — composição | `shaders/fullscreen.vert` + `shaders/composite.frag` | Soma cena + bloom e aplica vinheta. |

#### Vertex shader × fragment shader no passe principal

O `main.vert` faz três coisas:

```glsl
vec4 worldPos = u_model * vec4(a_position, 1.0);
v_normal = normalize(u_normalMatrix * a_normal);
v_uv = a_uv;

vec3 shadowWorld = worldPos.xyz + v_normal * 0.025;
v_lightSpacePos = u_lightVP * vec4(shadowWorld, 1.0);

gl_Position = u_projection * u_view * worldPos;
```

1. Leva o vértice do **espaço local** para o **mundo** (`u_model`).
2. Leva a **normal** para o mundo (`u_normalMatrix`).
3. Leva o vértice para o **espaço da luz** (`u_lightVP`) e para o **espaço de
   recorte** da câmera (`u_projection * u_view`).

Os valores `v_worldPos`, `v_normal`, `v_uv` e `v_lightSpacePos` são
**varyings**: saem do vertex shader, são interpolados pelo rasterizador e
entram no fragment shader. Eles **não** são atributos nem uniforms.

O `main.frag` usa esses valores para calcular a cor (iluminação, sombra, neblina
e emissão) — veja a seção 7.

#### Casos especiais: céu e fullscreen

O céu e o pós-processamento não desenham modelos 3D. Eles usam um único triângulo
que cobre a tela, gerado sem VBO:

```glsl
vec2 positions[3] = vec2[3](
    vec2(-1.0, -1.0),
    vec2( 3.0, -1.0),
    vec2(-1.0,  3.0)
);
```

O vertex shader usa `gl_VertexID` para escolher a posição de cada vértice. Por
isso, nesses programas **não há atributos de vértice**. O `sky.frag` usa
`u_invViewProj` para reconstruir a direção do raio de visão de cada pixel;
os shaders de bloom usam `v_uv` para amostrar texturas de tela.

#### O `depth.frag` vazio

No passe de profundidade, o fragment shader é praticamente vazio:

```glsl
void main()
{
    // O passe de profundidade não escreve cor: só o depth buffer importa.
}
```

Isso é intencional. O FBO da sombra não tem buffer de cor
(`glDrawBuffer(GL_NONE)`), apenas uma textura de profundidade. O importante é
o valor de `gl_FragCoord.z` que o OpenGL grava automaticamente no depth buffer.

### 5.3 Atributos de vértice

**Atributo de vértice** é um dado que acompanha cada vértice. No projeto, cada
vértice tem três atributos:

| Localização | Nome no shader | Tipo | O que representa |
|---|---|---|---|
| 0 | `a_position` | `vec3` | Posição do vértice no espaço local do objeto. |
| 1 | `a_normal` | `vec3` | Normal da superfície naquele vértice. |
| 2 | `a_uv` | `vec2` | Coordenada de textura. |

As localizações são fixadas antes de linkar o programa (`core/utils.py`):

```python
glBindAttribLocation(program, 0, "a_position")
glBindAttribLocation(program, 1, "a_normal")
glBindAttribLocation(program, 2, "a_uv")
```

Isso garante que o mesmo VAO funcione com o passe principal e com o passe de
profundidade.

#### Como o Mesh cria o VAO/VBO

`core/mesh.py` percorre `geometry.attributes` e, para cada atributo:

1. gera um VBO;
2. envia os dados com `glBufferData`;
3. habilita o atributo com `glEnableVertexAttribArray`;
4. descreve o formato com `glVertexAttribPointer(location, size, GL_FLOAT, ...)`.

As geometrias são trianguladas e **não usam índices**: cada triângulo repete os
vértices. Isso simplifica o Mesh e o VAO, seguindo a abordagem didática do livro.

#### Por que normal e UV existem

- **Normal**: sem ela, o fragment shader não consegue calcular
  `dot(normal, luz)` nem o especular. A normal também é usada no deslocamento
  contra *shadow acne*.
- **UV**: sem ela, não é possível amostrar a textura de imagem com
  `texture(u_texture, v_uv)`.

#### O passe de profundidade usa só `position`

O `depth.vert` declara apenas:

```glsl
layout(location = 0) in vec3 a_position;
```

Ele não precisa de normal nem de UV, porque só quer saber onde o vértice está
para gravar profundidade. O VAO continua tendo os três atributos; o shader
simplesmente ignora os que não declara.

### 5.4 Uniforms

**Uniform** é um valor constante para toda a chamada de desenho (ou para todo o
programa). Ele não muda por vértice nem por fragmento. É o canal para enviar
matrizes, cores, luzes, texturas e parâmetros do material.

| Conceito | Muda por... | Exemplo |
|---|---|---|
| Atributo | vértice | `a_position`, `a_normal`, `a_uv` |
| Uniform | draw call / programa | `u_model`, `u_view`, `u_lightColor` |
| Varying | sai do vertex e é interpolado até o fragment | `v_worldPos`, `v_normal`, `v_uv` |

#### Uniforms por quadro (câmera e luz)

Enviados em `core/renderer.py` antes de desenhar a cena:

| Uniform | Tipo | Papel |
|---|---|---|
| `u_view` | `mat4` | Matriz de visão da câmera. |
| `u_projection` | `mat4` | Projeção perspectiva. |
| `u_lightVP` | `mat4` | Visão × projeção ortográfica da luz. |
| `u_lightDirection` | `vec3` | Direção da superfície para a luz. |
| `u_lightColor` | `vec3` | Cor da luz direcional. |
| `u_ambientSky` / `u_ambientGround` | `vec3` | Ambiente hemisférico. |
| `u_cameraPos` | `vec3` | Posição da câmera (especular e neblina). |
| `u_fogColor`, `u_fogStart`, `u_fogEnd` | `vec3`, `float` | Neblina atmosférica. |
| `u_shadowEnabled` | `int` | Liga/desliga a sombra. |
| `u_shadowTexel` | `float` | Tamanho de um texel (`1/2048`). |
| `u_texture` / `u_shadowMap` | `sampler2D` | Unidades de textura 0 e 1. |

#### Uniforms por objeto e por material

Enviados em `_draw_mesh`, para cada nó com malha:

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

#### Uniforms do passe de profundidade

| Uniform | Tipo | Papel |
|---|---|---|
| `u_lightVP` | `mat4` | Mesma matriz da luz usada no passe principal. |
| `u_model` | `mat4` | Matriz global do objeto que está sendo desenhado. |

O `depth.frag` não tem uniforms de cor, material ou textura.

#### Uniforms do céu e do pós-processamento

| Programa | Uniforms | Papel |
|---|---|---|
| `sky.frag` | `u_invViewProj`, `u_cameraPos`, `u_sunDir`, `u_zenithColor`, `u_horizonColor`, `u_sunColor` | Reconstruir a direção do raio e desenhar gradiente/sol/estrelas. |
| `bloom_bright.frag` | `u_scene`, `u_threshold` | Extrair luminância acima do limiar. |
| `bloom_blur.frag` | `u_image`, `u_direction` | Borrar em uma direção (horizontal ou vertical). |
| `composite.frag` | `u_scene`, `u_bloom`, `u_bloomStrength` | Somar cena + bloom e aplicar vinheta. |

#### Como o uniform chega ao shader

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

### 5.5 Transformações

Cada `Object3D` tem `translation`, `rotation` (Euler em graus) e `scale`. A
matriz local é:

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

#### Do espaço local ao espaço de recorte

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

#### Câmera em perspectiva

A `OrbitCamera` calcula a posição da câmera a partir de `yaw`, `pitch`,
`distance` e `target`. Depois:

- `matrix.look_at(eye, target, up)` monta a matriz de visão;
- `matrix.perspective(fov_y, aspect, near, far)` monta a projeção.

A projeção perspectiva faz os objetos distantes parecerem menores e cria o
efeito de profundidade. O aspecto é recalculado quando a janela é redimensionada.

#### Matriz normal

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

#### A luz também tem câmera

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

## 6. Modelos e transformações

### 6.1 Disco voador (`scene/ufo.py`)

- Dois elipsoides achatados formam o casco inferior e superior.
- Toros formam o anel externo, o anel interno e a base da cúpula.
- A cúpula é uma esfera de vidro levemente achatada.
- Dez esferas emissivas no anel externo piscam em ciano e verde.
- Quatro painéis em caixa tornam a rotação do anel visível.
- Um cilindro escuro é o emissor do feixe; um cone transparente aditivo forma
  o feixe de varredura.
- Hierarquia: `ufo.root → ufo.body → anel → luzes/painéis`; o anel e o anel
  interno giram em sentidos opostos.
- O corpo oscila verticalmente e recebe inclinações (`bank`/`tilt`) calculadas
  pela missão.

### 6.2 Foguete (`scene/rocket.py`)

- Cilindro principal para a fuselagem, com textura de faixas e rebites.
- Cone para o nariz, esfera para a ponta e toro para o anel de reforço.
- Quatro aletas feitas com `PrismGeometry` (prisma triangular extrudado).
- Toro + esfera achatada formam a vigia (porthole).
- Cilindro escuro para o bocal; dois cones aditivos e uma esfera emissiva
  formam a chama e o brilho do motor.
- Dezoito esferas transparentes formam a fumaça, animadas por idade.
- Hierarquia: `rocket.root → rocket_body_group → peças`; a raiz recebe
  translação, rotação e a subida do salto. A chama e a fumaça são escaladas
  e reposicionadas ao longo do tempo.

### 6.3 Ambiente (`scene/environment.py`)

- Plano texturizado para o chão (UV repetido 20 × 20).
- Caixa para a plataforma, com textura de faixa de perigo e marcas de queima.
- Cilindros para o suporte central, mesetas e cactos.
- Caixas para a torre, vigas, bunker, porta, telhado e postes.
- Esferas escaladas para rochas e luzes de balizamento.
- Quatro braços de fixação rotacionados em 90° ao redor do foguete.

---

## 7. Iluminação, texturas e sombreamento de superfície

### 7.1 Texturas de imagem

O projeto usa **cinco texturas PNG**, todas geradas proceduralmente por
`tools/generate_textures.py` (não há imagens de terceiros):

| Arquivo | Uso |
|---|---|
| `textures/sand.png` | Chão do deserto, com ruído e ondulações. |
| `textures/metal_panels.png` | Torre, braços, suportes e peças metálicas. |
| `textures/rocket_body.png` | Fuselagem do foguete, com faixas e rebites. |
| `textures/pad.png` | Plataforma, faixa de perigo e marcas de queima. |
| `textures/ufo_hull.png` | Casco do disco voador. |

As texturas são carregadas por `core/texture.py` com `pygame.image.load`,
invertidas para a origem do OpenGL (`flipped=True`), enviadas com
`glTexImage2D`, recebem mipmaps e usam `GL_REPEAT`.

### 7.2 Coordenadas UV

- **Plano:** grade com `uv_repeat=(20, 20)` para repetir a areia.
- **Caixa:** cada face recebe UV de 0 a 1.
- **Esfera/elipsoide:** `u` ao longo da longitude e `v` ao longo da latitude.
- **Cilindro/cone:** `u` ao redor da circunferência e `v` ao longo da altura;
  as tampas usam coordenadas polares.
- **Toro:** `u` ao longo do anel maior e `v` ao longo do tubo.
- **Prisma:** UVs simples para as tampas e laterais.

### 7.3 Materiais

`core/material.py` define um material com:

- cor base (`color`), que multiplica a textura quando existir;
- coeficientes de Blinn-Phong (`specular`, `shininess`, `ambient`);
- emissão (`emissive`) para luzes, janelas, chamas e feixe;
- transparência (`opacity`, `transparent`, `additive`, `double_sided`);
- participação em sombras (`cast_shadow`, `receive_shadow`);
- modo sem iluminação (`unlit`) para elementos emissivos.

Os materiais são compartilhados por `scene/resources.py`, que também carrega
as texturas uma única vez.

### 7.4 Iluminação direcional

`core/light.py` define uma `DirectionalLight` com:

- direção de propagação `(-0.76, -0.40, 0.51)` normalizada;
- cor quente `(1.0, 0.88, 0.70)`;
- ambiente hemisférico: céu frio `(0.24, 0.31, 0.42)` e chão quente
  `(0.34, 0.26, 0.19)`.

No shader principal (`shaders/main.frag`) a superfície é sombreada com
Blinn-Phong:

```text
ambiente  = albedo · mix(ambiente_chão, ambiente_céu, normal.y·0.5 + 0.5)
difusa    = albedo · cor_da_luz · max(dot(normal, luz), 0)
especular = cor_especular · cor_da_luz · pow(max(dot(normal, halfway), 0), shininess)
cor       = ambiente + (difusa + especular) · sombra + emissivo
```

As normais são transformadas pela matriz normal
`transpose(inverse(upper-left 3×3 do modelo))`, evitando distorções quando há
escala não uniforme. Também há neblina atmosférica por distância para integrar
o chão ao horizonte.

### 7.5 Diferença: sombreamento de superfície × sombra projetada

Esta distinção é importante no projeto:

| Pergunta | Sombreamento de superfície | Sombra projetada |
|---|---|---|
| O que calcula? | A cor da superfície. | Se o ponto está oculto da luz. |
| Onde acontece? | `main.frag`, por fragmento. | Passe de profundidade + comparação no `main.frag`. |
| Depende de quê? | Normal, material, textura, luz, câmera. | Profundidade da cena vista da luz. |
| É calculado por objeto? | Sim, com os uniforms do material. | Não: é uma relação entre objetos. |
| Some quando `F` é desligado? | Não. O shading continua. | Sim. O fator de sombra vira 1.0. |
| Pode existir sem o outro? | Sim: dá para sombrear sem projetar sombra. | Não faz sentido sozinho: a sombra modula o shading. |

> **O sombreamento decide a cor da superfície; a sombra decide quanto da luz
> direta chega até ela. A sombra não substitui o sombreamento — ela o modula.**

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

1. **Divisão por `w`**: leva de espaço de recorte para NDC.
2. **`* 0.5 + 0.5`**: leva de `[-1, 1]` para `[0, 1]`, que é o intervalo da
   textura.
3. **Comparação**: se a profundidade do fragmento (`projected.z`) for maior que
   a menor profundidade gravada (`closest`), há um objeto na frente → sombra.
4. **PCF 3 × 3**: repete a comparação nos 9 texels vizinhos e faz a média. Isso
   suaviza a borda da sombra.
5. **Bias**: evita que o próprio fragmento se considere sombreado por causa de
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

Objetos transparentes (chamas, feixe, fumaça) não participam do passe de
profundidade (`cast_shadow = False`), e materiais como o chão, a plataforma e o
foguete recebem sombra (`receive_shadow = True`).

A tecla `F` alterna entre sombra ligada e desligada para comparação visual.

---

## 9. Pós-processamento e céu procedural (bônus)

Esses itens são opcionais e não substituem os requisitos principais.

### 9.1 Bloom

O pipeline é:

```text
cena → FBO da cena
     → bloom_bright (extrai brilho acima do limiar)
     → blur horizontal
     → blur vertical
     → composite (cena + bloom + vinheta)
```

O bloom é um efeito de tela, não de geometria. Por isso os shaders usam
`fullscreen.vert` e texturas (`u_scene`, `u_image`, `u_bloom`), sem atributos
de vértice 3D. A tecla `B` liga/desliga.

### 9.2 Céu procedural

`shaders/sky.frag` desenha um gradiente zênite-horizonte, um disco de sol com
halo, estrelas discretas no alto e *dithering* para reduzir banding. O céu é
desenhado com um único triângulo de tela cheia, sem VBO, usando `gl_VertexID`.

### 9.3 Texturas procedurais

Todas as texturas de imagem são geradas por `tools/generate_textures.py` com
ruído fractal periódico, desenho com Pillow e grão.

| Bloom ligado | Bloom desligado |
|---|---|
| ![Bloom ligado](screenshots/04_salto.png) | ![Bloom desligado](screenshots/bloom_off.png) |

---

## 10. Estrutura do projeto

```text
Base Aurora/
├── main.py                     # Janela, entrada, câmera, loop e screenshots
├── requirements.txt            # Dependências
├── README.md                   # Este documento
├── .gitignore
├── core/
│   ├── matrix.py               # Matrizes 4x4, perspectiva, look_at, normal matrix
│   ├── vector.py               # Vec3 e operações
│   ├── geometry.py             # Primitivas: caixa, plano, esfera, cilindro, cone, toro, prisma
│   ├── mesh.py                 # VAO/VBO e desenho
│   ├── material.py             # Parâmetros de material
│   ├── texture.py              # Carregamento de texturas de imagem
│   ├── object3d.py             # Hierarquia e transformações
│   ├── light.py                # Luz direcional e câmera orbital
│   ├── shader.py               # Programa GLSL e uniforms
│   ├── shadow.py               # FBO/textura de profundidade e matriz da luz
│   ├── postprocess.py          # Bloom (brilho, blur, composição)
│   ├── renderer.py             # Passe de sombra, passe principal, céu
│   ├── scene.py                # Raiz, câmera e luz
│   └── utils.py                # Caminhos, interpolação e compilação de shaders
├── scene/
│   ├── constants.py            # Constantes de layout
│   ├── resources.py            # Texturas e materiais compartilhados
│   ├── ufo.py                  # Modelo e animação do disco
│   ├── rocket.py               # Modelo, chama e fumaça do foguete
│   ├── environment.py          # Deserto, plataforma, torre, bunker, paisagem
│   └── mission.py              # Coreografia e interação por tempo
├── shaders/
│   ├── main.vert / main.frag
│   ├── depth.vert / depth.frag
│   ├── sky.vert / sky.frag
│   ├── fullscreen.vert
│   ├── bloom_bright.frag
│   ├── bloom_blur.frag
│   └── composite.frag
├── textures/                   # PNGs gerados por tools/generate_textures.py
├── tools/
│   └── generate_textures.py    # Geração procedural das texturas
└── screenshots/                # Imagens de documentação e comparação
```

---

## 11. Requisitos atendidos

| Requisito | Onde/Como |
|---|---|
| Tema disco voador + foguete | `scene/ufo.py`, `scene/rocket.py`. |
| Modelos 3D reconhecíveis com primitivas simples | Esferas, elipsoides, cilindros, cones, toros, caixas e prismas. |
| Animação controlada por tempo | `Mission.update(time)` e funções `phase`, `smoothstep`, `smootherstep`; `dt` só avança o tempo. |
| Translação, rotação e escala | `Object3D.translation/rotation/scale` e `matrix.compose`. |
| Transformações hierárquicas | `Object3D.add()` + `update_matrix()` com `M_pai · M_local`. |
| Câmera perspectiva controlável | `OrbitCamera` com yaw/pitch/zoom por teclado e aspecto dinâmico. |
| Pausar/retomar sem parar a visualização | `Espaço` alterna `self.paused`; a renderização continua. |
| Textura de imagem com UVs corretas | Cinco texturas PNG, UVs por primitiva, `core/texture.py`. |
| Iluminação direcional e materiais sensíveis à luz | `DirectionalLight` + Blinn-Phong em `main.frag`. |
| Normais corretas | `Geometry._fix_winding()`, `normal_matrix`, interpolação no shader. |
| Sombra projetada de elemento animado | Shadow mapping 2048², PCF 3×3, atualizado por quadro; visível no foguete, torre e disco. |
| Código-fonte, framework, shaders e texturas | Pastas `core/`, `scene/`, `shaders/`, `textures/`. |
| Arquivo de dependências | `requirements.txt`. |
| README com identificação, descrição, controles, fontes e declaração de IA | Este documento. |
| Bônus | Texturas procedurais, céu procedural, bloom e vinheta. |

---

## 12. Contribuições individuais

> Preencher com a divisão real de tarefas do grupo.

- **[Nome do integrante 1]:** [ex.: modelagem e animação do disco voador;
  shaders de céu e pós-processamento].
- **[Nome do integrante 2]:** [ex.: modelagem do foguete e do ambiente;
  texturas procedurais; iluminação].
- **[Nome do integrante 3]:** [ex.: framework, câmera, coreografia da missão;
  sombras; documentação].

---

## 13. Fontes e referências

- STEMKOSKI, Lee; PASCALE, Alexander. *Developing Graphics Frameworks with
  Python and OpenGL*. CRC Press, 2021. (framework base, câmera, iluminação e
  shadow mapping da seção 6.9)
- Pygame Community Edition — documentação oficial:
  <https://pyga.me/docs/>
- PyOpenGL — documentação:
  <https://pyopengl.sourceforge.net/documentation/>
- Khronos Group — OpenGL Wiki e especificação GLSL 3.30:
  <https://www.khronos.org/opengl/wiki/>
- LearnOpenGL — tutoriais de Blinn-Phong, shadow mapping e bloom:
  <https://learnopengl.com/>
- NumPy — documentação: <https://numpy.org/doc/>
- Pillow — documentação: <https://pillow.readthedocs.io/>

Não foram utilizados modelos 3D, imagens ou texturas de terceiros. Todas as
texturas são geradas proceduralmente pelo script do projeto.

---

## 14. Declaração de uso de IA

Ferramentas de inteligência artificial foram utilizadas como **apoio** ao
desenvolvimento, especialmente para:

- discutir a organização do framework e a separação em módulos;
- revisar e depurar shaders GLSL (iluminação, shadow mapping e bloom);
- sugerir ajustes de enquadramento, cores e intensidade de efeitos;
- revisar a redação deste README e a lista de requisitos.

Todo o código foi executado, testado e revisado pelos integrantes do grupo em
uma janela OpenGL real. A responsabilidade pelo conteúdo final, pela
originalidade e pelo funcionamento do trabalho é dos autores. Nenhum modelo,
textura ou outro recurso de terceiros foi incluído sem a devida referência.
