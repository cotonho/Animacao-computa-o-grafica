#version 330 core

in vec2 v_uv;
out vec4 FragColor;

uniform sampler2D u_scene;
uniform sampler2D u_bloom;
uniform float u_bloomStrength;

void main()
{
    vec3 sceneColor = texture(u_scene, v_uv).rgb;
    vec3 bloomColor = texture(u_bloom, v_uv).rgb;
    vec3 color = sceneColor + bloomColor * u_bloomStrength;

    // Vinheta discreta para valorizar o centro da composição.
    vec2 centered = v_uv - 0.5;
    color *= 1.0 - 0.22 * dot(centered, centered);

    FragColor = vec4(color, 1.0);
}
