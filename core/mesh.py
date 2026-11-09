"""Mesh: associa uma geometria a um material e cria o VAO/VBOs."""

from __future__ import annotations

import numpy as np
from OpenGL.GL import (
    GL_ARRAY_BUFFER,
    GL_FLOAT,
    GL_STATIC_DRAW,
    GL_TRIANGLES,
    glBindBuffer,
    glBindVertexArray,
    glBufferData,
    glDeleteBuffers,
    glDeleteVertexArrays,
    glDrawArrays,
    glEnableVertexAttribArray,
    glGenBuffers,
    glGenVertexArrays,
    glVertexAttribPointer,
)

from .geometry import Geometry
from .material import Material

# As localizações são fixadas em utils.create_program (glBindAttribLocation).
ATTRIBUTE_LOCATIONS = {"position": 0, "normal": 1, "uv": 2}
ATTRIBUTE_SIZES = {"position": 3, "normal": 3, "uv": 2}


class Mesh:
    def __init__(self, geometry: Geometry, material: Material):
        self.geometry = geometry
        self.material = material
        self.vao = glGenVertexArrays(1)
        self.buffers: dict[str, int] = {}

        glBindVertexArray(self.vao)
        for name, data in geometry.attributes.items():
            location = ATTRIBUTE_LOCATIONS[name]
            size = ATTRIBUTE_SIZES[name]
            buffer = glGenBuffers(1)
            self.buffers[name] = buffer
            glBindBuffer(GL_ARRAY_BUFFER, buffer)
            glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, GL_STATIC_DRAW)
            glEnableVertexAttribArray(location)
            glVertexAttribPointer(location, size, GL_FLOAT, False, 0, None)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def draw(self) -> None:
        glBindVertexArray(self.vao)
        glDrawArrays(self.geometry.draw_mode or GL_TRIANGLES, 0, self.geometry.vertex_count)
        glBindVertexArray(0)

    def destroy(self) -> None:
        glDeleteBuffers(len(self.buffers), list(self.buffers.values()))
        glDeleteVertexArrays(1, [self.vao])
