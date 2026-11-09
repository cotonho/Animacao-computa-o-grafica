"""Funções utilitárias: caminhos, interpolação, leitura de shaders."""

from __future__ import annotations

import math
import os
from pathlib import Path

from OpenGL.GL import (
    GL_COMPILE_STATUS,
    GL_FRAGMENT_SHADER,
    GL_LINK_STATUS,
    GL_VERTEX_SHADER,
    glAttachShader,
    glBindAttribLocation,
    glCompileShader,
    glCreateProgram,
    glCreateShader,
    glDeleteShader,
    glGetProgramInfoLog,
    glGetProgramiv,
    glGetShaderInfoLog,
    glGetShaderiv,
    glLinkProgram,
    glShaderSource,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
SHADER_DIR = ROOT_DIR / "shaders"
TEXTURE_DIR = ROOT_DIR / "textures"


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def smoothstep(t: float) -> float:
    t = clamp(t)
    return t * t * (3.0 - 2.0 * t)


def smootherstep(t: float) -> float:
    t = clamp(t)
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def ease_in_cubic(t: float) -> float:
    t = clamp(t)
    return t * t * t


def ease_out_cubic(t: float) -> float:
    t = clamp(t)
    return 1.0 - (1.0 - t) ** 3


def phase(time: float, start: float, end: float) -> float:
    """Normaliza ``time`` no intervalo [start, end], saturando em 0..1."""
    if end <= start:
        return 0.0
    return clamp((time - start) / (end - start))


def pulse(time: float, frequency: float = 1.0) -> float:
    """Onda suave no intervalo 0..1, útil para luzes pulsantes."""
    return 0.5 + 0.5 * math.sin(time * frequency * math.tau)


def read_shader(filename: str) -> str:
    path = SHADER_DIR / filename
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def compile_shader(source: str, shader_type: int) -> int:
    shader = glCreateShader(shader_type)
    glShaderSource(shader, source)
    glCompileShader(shader)
    if not glGetShaderiv(shader, GL_COMPILE_STATUS):
        label = "vertex" if shader_type == GL_VERTEX_SHADER else "fragment"
        raise RuntimeError(
            f"Erro ao compilar shader {label}:\n{glGetShaderInfoLog(shader).decode()}"
        )
    return shader


def create_program(vertex_file: str, fragment_file: str) -> int:
    vertex_shader = compile_shader(read_shader(vertex_file), GL_VERTEX_SHADER)
    fragment_shader = compile_shader(read_shader(fragment_file), GL_FRAGMENT_SHADER)

    program = glCreateProgram()
    glAttachShader(program, vertex_shader)
    glAttachShader(program, fragment_shader)

    # Localizações fixas dos atributos: o mesmo VAO funciona com todos os
    # programas (principal, profundidade, etc.).
    glBindAttribLocation(program, 0, "a_position")
    glBindAttribLocation(program, 1, "a_normal")
    glBindAttribLocation(program, 2, "a_uv")

    glLinkProgram(program)
    if not glGetProgramiv(program, GL_LINK_STATUS):
        raise RuntimeError(f"Erro ao linkar programa:\n{glGetProgramInfoLog(program).decode()}")

    glDeleteShader(vertex_shader)
    glDeleteShader(fragment_shader)
    return program


def texture_path(filename: str) -> str:
    return os.fspath(TEXTURE_DIR / filename)
