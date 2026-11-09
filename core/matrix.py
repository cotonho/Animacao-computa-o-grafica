"""Matrizes 4x4 e transformações geométricas.

Convenção adotada em todo o projeto (igual à usada no livro):
  * vetores são colunas:  p' = M @ p
  * as matrizes são arrays NumPy com linhas/colunas na ordem matemática usual
  * ao enviar para a GPU usamos glUniformMatrix4fv(..., GL_TRUE, ...), que
    transpõe o array para o formato column-major esperado pelo OpenGL.

Isso mantém o código em Python legível (M[linha, coluna]) sem abrir mão da
convenção do OpenGL/GLSL.
"""

from __future__ import annotations

import math

import numpy as np


def identity() -> np.ndarray:
    return np.identity(4, dtype=np.float64)


def translation(x: float, y: float, z: float) -> np.ndarray:
    m = identity()
    m[0, 3] = x
    m[1, 3] = y
    m[2, 3] = z
    return m


def scale(x: float, y: float, z: float) -> np.ndarray:
    m = identity()
    m[0, 0] = x
    m[1, 1] = y
    m[2, 2] = z
    return m


def rotation_x(angle_degrees: float) -> np.ndarray:
    a = math.radians(angle_degrees)
    c, s = math.cos(a), math.sin(a)
    m = identity()
    m[1, 1] = c
    m[1, 2] = -s
    m[2, 1] = s
    m[2, 2] = c
    return m


def rotation_y(angle_degrees: float) -> np.ndarray:
    a = math.radians(angle_degrees)
    c, s = math.cos(a), math.sin(a)
    m = identity()
    m[0, 0] = c
    m[0, 2] = s
    m[2, 0] = -s
    m[2, 2] = c
    return m


def rotation_z(angle_degrees: float) -> np.ndarray:
    a = math.radians(angle_degrees)
    c, s = math.cos(a), math.sin(a)
    m = identity()
    m[0, 0] = c
    m[0, 1] = -s
    m[1, 0] = s
    m[1, 1] = c
    return m


def rotation(rx: float, ry: float, rz: float) -> np.ndarray:
    """Rotação de Euler: primeiro X, depois Y, depois Z (Rz @ Ry @ Rx)."""
    return rotation_z(rz) @ rotation_y(ry) @ rotation_x(rx)


def compose(
    position: tuple[float, float, float] | np.ndarray,
    rotation_degrees: tuple[float, float, float] | np.ndarray,
    scale_factors: tuple[float, float, float] | np.ndarray,
) -> np.ndarray:
    """Matriz local T @ R @ S."""
    return (
        translation(*position)
        @ rotation(*rotation_degrees)
        @ scale(*scale_factors)
    )


def multiply(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return a @ b


def perspective(
    fov_y_degrees: float, aspect: float, near: float, far: float
) -> np.ndarray:
    f = 1.0 / math.tan(math.radians(fov_y_degrees) / 2.0)
    m = np.zeros((4, 4), dtype=np.float64)
    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = (far + near) / (near - far)
    m[2, 3] = (2.0 * far * near) / (near - far)
    m[3, 2] = -1.0
    return m


def orthographic(
    left: float, right: float, bottom: float, top: float, near: float, far: float
) -> np.ndarray:
    m = identity()
    m[0, 0] = 2.0 / (right - left)
    m[1, 1] = 2.0 / (top - bottom)
    m[2, 2] = -2.0 / (far - near)
    m[0, 3] = -(right + left) / (right - left)
    m[1, 3] = -(top + bottom) / (top - bottom)
    m[2, 3] = -(far + near) / (far - near)
    return m


def look_at(
    eye: tuple[float, float, float] | np.ndarray,
    target: tuple[float, float, float] | np.ndarray,
    up: tuple[float, float, float] | np.ndarray = (0.0, 1.0, 0.0),
) -> np.ndarray:
    eye = np.asarray(eye, dtype=np.float64)
    target = np.asarray(target, dtype=np.float64)
    up = np.asarray(up, dtype=np.float64)

    forward = target - eye
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, up)
    right /= np.linalg.norm(right)
    true_up = np.cross(right, forward)

    m = identity()
    m[0, :3] = right
    m[1, :3] = true_up
    m[2, :3] = -forward
    m[0, 3] = -np.dot(right, eye)
    m[1, 3] = -np.dot(true_up, eye)
    m[2, 3] = np.dot(forward, eye)
    return m


def inverse(m: np.ndarray) -> np.ndarray:
    return np.linalg.inv(m)


def normal_matrix(model: np.ndarray) -> np.ndarray:
    """Matriz 3x3 para normais: transpose(inverse(upper-left 3x3))."""
    return np.linalg.inv(model[:3, :3]).T


def transform_point(m: np.ndarray, point: tuple[float, float, float]) -> np.ndarray:
    p = np.array([point[0], point[1], point[2], 1.0], dtype=np.float64)
    return (m @ p)[:3]


def transform_direction(m: np.ndarray, direction: tuple[float, float, float]) -> np.ndarray:
    d = np.array([direction[0], direction[1], direction[2], 0.0], dtype=np.float64)
    return (m @ d)[:3]
