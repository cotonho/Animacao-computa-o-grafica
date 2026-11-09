"""Envoltório fino para programas GLSL e envio de uniforms."""

from __future__ import annotations

import numpy as np
from OpenGL.GL import (
    GL_FLOAT,
    GL_TRUE,
    glGetUniformLocation,
    glUniform1f,
    glUniform1i,
    glUniform2f,
    glUniform3f,
    glUniformMatrix3fv,
    glUniformMatrix4fv,
    glUseProgram,
)

from .utils import create_program


class ShaderProgram:
    def __init__(self, vertex_file: str, fragment_file: str):
        self.program = create_program(vertex_file, fragment_file)
        self._locations: dict[str, int] = {}

    def use(self) -> None:
        glUseProgram(self.program)

    def location(self, name: str) -> int:
        if name not in self._locations:
            self._locations[name] = glGetUniformLocation(self.program, name)
        return self._locations[name]

    # ------------------------------------------------------------------
    def set_int(self, name: str, value: int) -> None:
        glUniform1i(self.location(name), int(value))

    def set_float(self, name: str, value: float) -> None:
        glUniform1f(self.location(name), float(value))

    def set_vec2(self, name: str, x: float, y: float) -> None:
        glUniform2f(self.location(name), float(x), float(y))

    def set_vec3(self, name: str, value) -> None:
        glUniform3f(self.location(name), float(value[0]), float(value[1]), float(value[2]))

    def set_mat3(self, name: str, matrix: np.ndarray) -> None:
        data = np.ascontiguousarray(matrix, dtype=np.float32)
        glUniformMatrix3fv(self.location(name), 1, GL_TRUE, data)

    def set_mat4(self, name: str, matrix: np.ndarray) -> None:
        data = np.ascontiguousarray(matrix, dtype=np.float32)
        glUniformMatrix4fv(self.location(name), 1, GL_TRUE, data)

    def set_texture(self, name: str, unit: int) -> None:
        self.set_int(name, unit)
