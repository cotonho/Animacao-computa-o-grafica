#version 330 core

in vec2 v_uv;
out vec4 FragColor;

uniform sampler2D u_image;
uniform vec2 u_direction;   // deslocamento em unidades de textura

const float weights[5] = float[5](
    0.227027, 0.1945946, 0.1216216, 0.054054, 0.016216
);

void main()
{
    vec3 result = texture(u_image, v_uv).rgb * weights[0];
    for (int i = 1; i < 5; ++i) {
        vec2 offset = u_direction * float(i);
        result += texture(u_image, v_uv + offset).rgb * weights[i];
        result += texture(u_image, v_uv - offset).rgb * weights[i];
    }
    FragColor = vec4(result, 1.0);
}
