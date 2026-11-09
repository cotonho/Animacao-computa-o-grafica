#version 330 core

in vec2 v_uv;
out vec4 FragColor;

uniform sampler2D u_scene;
uniform float u_threshold;

void main()
{
    vec3 color = texture(u_scene, v_uv).rgb;
    float luminance = dot(color, vec3(0.2126, 0.7152, 0.0722));
    float contribution = smoothstep(u_threshold, u_threshold + 0.25, luminance);
    FragColor = vec4(color * contribution, 1.0);
}
