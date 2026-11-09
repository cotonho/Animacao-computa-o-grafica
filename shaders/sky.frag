#version 330 core

in vec2 v_ndc;
out vec4 FragColor;

uniform mat4 u_invViewProj;
uniform vec3 u_cameraPos;
uniform vec3 u_sunDir;       // direção da câmera para o sol
uniform vec3 u_zenithColor;
uniform vec3 u_horizonColor;
uniform vec3 u_sunColor;

float hash13(vec3 p)
{
    p = fract(p * 0.1031);
    p += dot(p, p.yzx + 33.33);
    return fract((p.x + p.y) * p.z);
}

void main()
{
    vec4 world = u_invViewProj * vec4(v_ndc, 1.0, 1.0);
    vec3 direction = normalize(world.xyz / world.w - u_cameraPos);

    float height = clamp(direction.y, -1.0, 1.0);
    float gradient = smoothstep(0.0, 0.24, height);
    vec3 color = mix(u_horizonColor, u_zenithColor, gradient);

    // Banda de brilho junto ao horizonte.
    color += u_sunColor * exp(-abs(height) * 9.0) * 0.18;

    // Disco e halo do sol.
    float sun = max(dot(direction, normalize(u_sunDir)), 0.0);
    color += u_sunColor * (pow(sun, 900.0) * 2.0 + pow(sun, 14.0) * 0.30);

    // Estrelas discretas no alto do céu.
    float star = step(0.9985, hash13(floor(direction * 650.0)));
    color += vec3(star) * smoothstep(0.15, 0.65, height) * 0.9;

    // Dithering leve para reduzir banding no gradiente de 8 bits.
    color += (hash13(vec3(gl_FragCoord.xy, 1.0)) - 0.5) / 255.0;

    FragColor = vec4(color, 1.0);
}
