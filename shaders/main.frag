#version 330 core

in vec3 v_worldPos;
in vec3 v_normal;
in vec2 v_uv;
in vec4 v_lightSpacePos;

out vec4 FragColor;

// Material
uniform vec3 u_baseColor;
uniform vec3 u_specularColor;
uniform float u_shininess;
uniform float u_ambientStrength;
uniform vec3 u_emissive;
uniform float u_opacity;
uniform int u_useTexture;
uniform int u_unlit;
uniform sampler2D u_texture;

// Iluminação direcional
uniform vec3 u_lightDirection;   // vetor unitário da superfície para a luz
uniform vec3 u_lightColor;
uniform vec3 u_ambientSky;
uniform vec3 u_ambientGround;
uniform vec3 u_cameraPos;

// Sombra projetada
uniform sampler2D u_shadowMap;
uniform float u_shadowTexel;
uniform int u_shadowEnabled;
uniform int u_receiveShadow;

// Neblina atmosférica
uniform vec3 u_fogColor;
uniform float u_fogStart;
uniform float u_fogEnd;

float shadowFactor(vec3 normal, vec3 lightDir)
{
    if (u_shadowEnabled == 0 || u_receiveShadow == 0) {
        return 1.0;
    }

    vec3 projected = v_lightSpacePos.xyz / v_lightSpacePos.w;
    projected = projected * 0.5 + 0.5;

    if (projected.x < 0.0 || projected.x > 1.0 ||
        projected.y < 0.0 || projected.y > 1.0 ||
        projected.z > 1.0) {
        return 1.0;
    }

    float bias = max(0.0018 * (1.0 - dot(normal, lightDir)), 0.0005);
    float visibility = 0.0;

    // PCF 3x3: média de nove comparações de profundidade.
    for (int x = -1; x <= 1; ++x) {
        for (int y = -1; y <= 1; ++y) {
            vec2 offset = vec2(float(x), float(y)) * u_shadowTexel;
            float closest = texture(u_shadowMap, projected.xy + offset).r;
            visibility += (projected.z - bias > closest) ? 0.0 : 1.0;
        }
    }
    return visibility / 9.0;
}

void main()
{
    vec3 albedo = u_baseColor;
    float alpha = u_opacity;
    if (u_useTexture == 1) {
        vec4 texel = texture(u_texture, v_uv);
        albedo *= texel.rgb;
        alpha *= texel.a;
    }

    vec3 color;
    if (u_unlit == 1) {
        color = albedo + u_emissive;
    } else {
        vec3 normal = normalize(v_normal);
        vec3 lightDir = normalize(u_lightDirection);
        vec3 viewDir = normalize(u_cameraPos - v_worldPos);
        vec3 halfway = normalize(lightDir + viewDir);

        float nDotL = max(dot(normal, lightDir), 0.0);
        float specularAmount = pow(max(dot(normal, halfway), 0.0), max(u_shininess, 1.0));

        // Ambiente hemisférico: céu frio por cima, areia quente por baixo.
        vec3 hemisphere = mix(u_ambientGround, u_ambientSky, normal.y * 0.5 + 0.5);
        vec3 ambient = albedo * hemisphere * u_ambientStrength;
        vec3 diffuse = albedo * u_lightColor * nDotL;
        vec3 specular = u_specularColor * u_lightColor * specularAmount * nDotL;

        float shadow = shadowFactor(normal, lightDir);
        color = ambient + (diffuse + specular) * shadow + u_emissive;
    }

    // Neblina por distância, integrando o chão ao horizonte.
    float distanceToCamera = length(u_cameraPos - v_worldPos);
    float fog = smoothstep(u_fogStart, u_fogEnd, distanceToCamera);
    color = mix(color, u_fogColor, fog);

    FragColor = vec4(color, alpha);
}
