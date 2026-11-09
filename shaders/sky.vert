#version 330 core

out vec2 v_ndc;

void main()
{
    // Triângulo que cobre a tela inteira, sem VBO.
    vec2 positions[3] = vec2[3](
        vec2(-1.0, -1.0),
        vec2( 3.0, -1.0),
        vec2(-1.0,  3.0)
    );
    v_ndc = positions[gl_VertexID];
    gl_Position = vec4(v_ndc, 0.999, 1.0);
}
