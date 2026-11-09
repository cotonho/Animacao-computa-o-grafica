"""Geometrias primitivas construídas manualmente.

Cada geometria guarda três atributos de vértice, exatamente os utilizados
pelos shaders do projeto:

    position : vec3
    normal   : vec3
    uv       : vec2

Não usamos índices: as listas já vêm trianguladas, o que mantém o Mesh e o
VAO simples e didáticos (mesma abordagem do framework do livro).
"""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np
from OpenGL.GL import GL_TRIANGLES

Vec2 = tuple[float, float]
Vec3Tuple = tuple[float, float, float]


class Geometry:
    def __init__(
        self,
        attributes: dict[str, np.ndarray],
        draw_mode: int = GL_TRIANGLES,
        fix_winding: bool = True,
    ):
        self.attributes = {
            name: np.asarray(values, dtype=np.float32)
            for name, values in attributes.items()
        }
        self.draw_mode = draw_mode
        self.vertex_count = len(self.attributes["position"])
        if fix_winding:
            self._fix_winding()

    # ------------------------------------------------------------------
    def _fix_winding(self) -> None:
        """Garante que cada triângulo tenha winding anti-horário visto de fora.

        A orientação é comparada com a média das normais dos três vértices.
        Isso permite escrever os geradores de forma direta e deixa a
        consistência para este passo.
        """
        if "normal" not in self.attributes:
            return
        position = self.attributes["position"]
        normal = self.attributes["normal"]
        for base in range(0, self.vertex_count, 3):
            p0, p1, p2 = position[base : base + 3]
            face_normal = np.cross(p1 - p0, p2 - p0)
            average_normal = normal[base : base + 3].sum(axis=0)
            if np.dot(face_normal, average_normal) < 0.0:
                for attribute in self.attributes.values():
                    attribute[[base + 1, base + 2]] = attribute[[base + 2, base + 1]]


# ----------------------------------------------------------------------
# caixa
# ----------------------------------------------------------------------
def _quad(
    positions: list[Vec3Tuple],
    normals: list[Vec3Tuple],
    uvs: list[Vec2],
    p0: Vec3Tuple,
    p1: Vec3Tuple,
    p2: Vec3Tuple,
    p3: Vec3Tuple,
    normal: Vec3Tuple,
) -> None:
    for p in (p0, p1, p2, p0, p2, p3):
        positions.append(p)
        normals.append(normal)
    uvs.extend([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 0.0), (1.0, 1.0), (0.0, 1.0)])


class BoxGeometry(Geometry):
    def __init__(self, width: float = 1.0, height: float = 1.0, depth: float = 1.0):
        w, h, d = width / 2.0, height / 2.0, depth / 2.0
        positions: list[Vec3Tuple] = []
        normals: list[Vec3Tuple] = []
        uvs: list[Vec2] = []

        _quad(positions, normals, uvs, (w, -h, d), (w, -h, -d), (w, h, -d), (w, h, d), (1, 0, 0))
        _quad(positions, normals, uvs, (-w, -h, -d), (-w, -h, d), (-w, h, d), (-w, h, -d), (-1, 0, 0))
        _quad(positions, normals, uvs, (-w, h, d), (w, h, d), (w, h, -d), (-w, h, -d), (0, 1, 0))
        _quad(positions, normals, uvs, (-w, -h, -d), (w, -h, -d), (w, -h, d), (-w, -h, d), (0, -1, 0))
        _quad(positions, normals, uvs, (-w, -h, d), (w, -h, d), (w, h, d), (-w, h, d), (0, 0, 1))
        _quad(positions, normals, uvs, (w, -h, -d), (-w, -h, -d), (-w, h, -d), (w, h, -d), (0, 0, -1))

        super().__init__({"position": positions, "normal": normals, "uv": uvs})


# ----------------------------------------------------------------------
# plano (XZ, normal +Y)
# ----------------------------------------------------------------------
class PlaneGeometry(Geometry):
    def __init__(
        self,
        width: float = 1.0,
        depth: float = 1.0,
        segments_x: int = 1,
        segments_z: int = 1,
        uv_repeat: tuple[float, float] = (1.0, 1.0),
    ):
        positions: list[Vec3Tuple] = []
        normals: list[Vec3Tuple] = []
        uvs: list[Vec2] = []

        for ix in range(segments_x):
            x0 = -width / 2.0 + width * ix / segments_x
            x1 = -width / 2.0 + width * (ix + 1) / segments_x
            for iz in range(segments_z):
                z0 = -depth / 2.0 + depth * iz / segments_z
                z1 = -depth / 2.0 + depth * (iz + 1) / segments_z
                u0 = ix / segments_x * uv_repeat[0]
                u1 = (ix + 1) / segments_x * uv_repeat[0]
                v0 = iz / segments_z * uv_repeat[1]
                v1 = (iz + 1) / segments_z * uv_repeat[1]

                p0 = (x0, 0.0, z0)
                p1 = (x0, 0.0, z1)
                p2 = (x1, 0.0, z1)
                p3 = (x1, 0.0, z0)
                for p, uv in (
                    (p0, (u0, v0)),
                    (p1, (u0, v1)),
                    (p2, (u1, v1)),
                    (p0, (u0, v0)),
                    (p2, (u1, v1)),
                    (p3, (u1, v0)),
                ):
                    positions.append(p)
                    normals.append((0.0, 1.0, 0.0))
                    uvs.append(uv)

        super().__init__({"position": positions, "normal": normals, "uv": uvs})


# ----------------------------------------------------------------------
# esfera / elipsoide
# ----------------------------------------------------------------------
class SphereGeometry(Geometry):
    def __init__(self, radius: float = 1.0, sectors: int = 32, stacks: int = 16):
        grid_positions: list[Vec3Tuple] = []
        grid_normals: list[Vec3Tuple] = []
        grid_uvs: list[Vec2] = []

        for i in range(stacks + 1):
            v = i / stacks
            phi = math.pi * v
            y = math.cos(phi) * radius
            ring = math.sin(phi) * radius
            for j in range(sectors + 1):
                u = j / sectors
                theta = math.tau * u
                x = math.cos(theta) * ring
                z = math.sin(theta) * ring
                grid_positions.append((x, y, z))
                grid_normals.append((x / radius, y / radius, z / radius))
                grid_uvs.append((u, 1.0 - v))

        positions: list[Vec3Tuple] = []
        normals: list[Vec3Tuple] = []
        uvs: list[Vec2] = []
        for i in range(stacks):
            for j in range(sectors):
                a = i * (sectors + 1) + j
                b = a + sectors + 1
                for index in (a, b, b + 1, a, b + 1, a + 1):
                    positions.append(grid_positions[index])
                    normals.append(grid_normals[index])
                    uvs.append(grid_uvs[index])

        super().__init__({"position": positions, "normal": normals, "uv": uvs})


class EllipsoidGeometry(Geometry):
    def __init__(
        self,
        radius_x: float = 1.0,
        radius_y: float = 1.0,
        radius_z: float = 1.0,
        sectors: int = 32,
        stacks: int = 16,
    ):
        sphere = SphereGeometry(1.0, sectors, stacks)
        positions = sphere.attributes["position"].copy()
        positions[:, 0] *= radius_x
        positions[:, 1] *= radius_y
        positions[:, 2] *= radius_z
        normals = positions / np.array(
            [radius_x * radius_x, radius_y * radius_y, radius_z * radius_z],
            dtype=np.float32,
        )
        normals /= np.linalg.norm(normals, axis=1, keepdims=True)
        super().__init__(
            {
                "position": positions,
                "normal": normals,
                "uv": sphere.attributes["uv"],
            }
        )


# ----------------------------------------------------------------------
# cilindro / cone
# ----------------------------------------------------------------------
class CylinderGeometry(Geometry):
    def __init__(
        self,
        radius_top: float = 1.0,
        radius_bottom: float = 1.0,
        height: float = 2.0,
        radial_segments: int = 32,
        height_segments: int = 1,
        cap_top: bool = True,
        cap_bottom: bool = True,
    ):
        positions: list[Vec3Tuple] = []
        normals: list[Vec3Tuple] = []
        uvs: list[Vec2] = []

        slope = (radius_bottom - radius_top) / height if height else 0.0
        for iy in range(height_segments):
            v0 = iy / height_segments
            v1 = (iy + 1) / height_segments
            y0 = -height / 2.0 + height * v0
            y1 = -height / 2.0 + height * v1
            r0 = radius_bottom + (radius_top - radius_bottom) * v0
            r1 = radius_bottom + (radius_top - radius_bottom) * v1
            for j in range(radial_segments):
                u0 = 1.0 - j / radial_segments
                u1 = 1.0 - (j + 1) / radial_segments
                t0 = math.tau * u0
                t1 = math.tau * u1
                c0, s0 = math.cos(t0), math.sin(t0)
                c1, s1 = math.cos(t1), math.sin(t1)

                p00 = (c0 * r0, y0, s0 * r0)
                p10 = (c1 * r0, y0, s1 * r0)
                p11 = (c1 * r1, y1, s1 * r1)
                p01 = (c0 * r1, y1, s0 * r1)
                n00 = np.array((c0, slope, s0), dtype=float)
                n10 = np.array((c1, slope, s1), dtype=float)
                n00 /= np.linalg.norm(n00)
                n10 /= np.linalg.norm(n10)

                for p, n, uv in (
                    (p00, n00, (u0, v0)),
                    (p10, n10, (u1, v0)),
                    (p11, n10, (u1, v1)),
                    (p00, n00, (u0, v0)),
                    (p11, n10, (u1, v1)),
                    (p01, n00, (u0, v1)),
                ):
                    positions.append(tuple(p))
                    normals.append(tuple(n))
                    uvs.append(uv)

        # tampas
        def add_cap(radius: float, y: float, normal_y: float, v: float) -> None:
            if radius <= 0.0:
                return
            center = (0.0, y, 0.0)
            for j in range(radial_segments):
                t0 = math.tau * j / radial_segments
                t1 = math.tau * (j + 1) / radial_segments
                p0 = (math.cos(t0) * radius, y, math.sin(t0) * radius)
                p1 = (math.cos(t1) * radius, y, math.sin(t1) * radius)
                for p, uv in (
                    (center, (0.5, 0.5)),
                    (p0, (math.cos(t0) * 0.5 + 0.5, math.sin(t0) * 0.5 + 0.5)),
                    (p1, (math.cos(t1) * 0.5 + 0.5, math.sin(t1) * 0.5 + 0.5)),
                ):
                    positions.append(p)
                    normals.append((0.0, normal_y, 0.0))
                    uvs.append(uv)

        if cap_top:
            add_cap(radius_top, height / 2.0, 1.0, 1.0)
        if cap_bottom:
            add_cap(radius_bottom, -height / 2.0, -1.0, 0.0)

        super().__init__({"position": positions, "normal": normals, "uv": uvs})


class ConeGeometry(Geometry):
    """Cone de revolução.

    origin="base": base em y=0 e ponta em y=+height (nariz de foguete).
    origin="apex": ponta em y=0 e base em y=-height (feixe/cone de luz).
    """

    def __init__(
        self,
        radius: float = 1.0,
        height: float = 1.0,
        radial_segments: int = 32,
        cap: bool = True,
        origin: str = "base",
    ):
        cylinder = CylinderGeometry(
            radius_top=0.0,
            radius_bottom=radius,
            height=height,
            radial_segments=radial_segments,
            cap_top=False,
            cap_bottom=cap,
        )
        positions = cylinder.attributes["position"].copy()
        if origin == "base":
            positions[:, 1] += height / 2.0
        elif origin == "apex":
            positions[:, 1] -= height / 2.0
        else:
            raise ValueError("origin deve ser 'base' ou 'apex'")
        super().__init__(
            {
                "position": positions,
                "normal": cylinder.attributes["normal"],
                "uv": cylinder.attributes["uv"],
            }
        )


# ----------------------------------------------------------------------
# toro (anel do disco voador)
# ----------------------------------------------------------------------
class TorusGeometry(Geometry):
    def __init__(
        self,
        major_radius: float = 1.0,
        minor_radius: float = 0.2,
        major_segments: int = 48,
        minor_segments: int = 16,
    ):
        positions: list[Vec3Tuple] = []
        normals: list[Vec3Tuple] = []
        uvs: list[Vec2] = []

        for i in range(major_segments + 1):
            u = i / major_segments
            theta = math.tau * u
            cos_t, sin_t = math.cos(theta), math.sin(theta)
            for j in range(minor_segments + 1):
                v = j / minor_segments
                phi = math.tau * v
                cos_p, sin_p = math.cos(phi), math.sin(phi)
                normal = (cos_p * cos_t, sin_p, cos_p * sin_t)
                position = (
                    (major_radius + minor_radius * cos_p) * cos_t,
                    minor_radius * sin_p,
                    (major_radius + minor_radius * cos_p) * sin_t,
                )
                positions.append(position)
                normals.append(normal)
                uvs.append((u, v))

        stride = minor_segments + 1
        triangles_positions: list[Vec3Tuple] = []
        triangles_normals: list[Vec3Tuple] = []
        triangles_uvs: list[Vec2] = []
        for i in range(major_segments):
            for j in range(minor_segments):
                a = i * stride + j
                b = (i + 1) * stride + j
                for idx, uv in (
                    (a, uvs[a]),
                    (b, uvs[b]),
                    (b + 1, uvs[b + 1]),
                    (a, uvs[a]),
                    (b + 1, uvs[b + 1]),
                    (a + 1, uvs[a + 1]),
                ):
                    triangles_positions.append(positions[idx])
                    triangles_normals.append(normals[idx])
                    triangles_uvs.append(uv)

        super().__init__(
            {
                "position": triangles_positions,
                "normal": triangles_normals,
                "uv": triangles_uvs,
            }
        )


# ----------------------------------------------------------------------
# prisma extrudado (aletas, braços e peças)
# ----------------------------------------------------------------------
class PrismGeometry(Geometry):
    def __init__(self, points: Iterable[Vec2], depth: float = 0.1):
        points = list(points)
        if len(points) < 3:
            raise ValueError("Um prisma precisa de pelo menos 3 pontos")
        z_front = depth / 2.0
        z_back = -depth / 2.0

        positions: list[Vec3Tuple] = []
        normals: list[Vec3Tuple] = []
        uvs: list[Vec2] = []

        # tampas (leque; os polígonos usados no projeto são convexos)
        for i in range(1, len(points) - 1):
            p0, p1, p2 = points[0], points[i], points[i + 1]
            for p, normal in (
                ((p0[0], p0[1], z_front), (0, 0, 1)),
                ((p1[0], p1[1], z_front), (0, 0, 1)),
                ((p2[0], p2[1], z_front), (0, 0, 1)),
                ((p0[0], p0[1], z_back), (0, 0, -1)),
                ((p2[0], p2[1], z_back), (0, 0, -1)),
                ((p1[0], p1[1], z_back), (0, 0, -1)),
            ):
                positions.append(p)
                normals.append(normal)
                uvs.append((p[0] * 0.5 + 0.5, p[1] * 0.5 + 0.5))

        # laterais
        for i in range(len(points)):
            p0 = points[i]
            p1 = points[(i + 1) % len(points)]
            edge = (p1[0] - p0[0], p1[1] - p0[1])
            normal = (edge[1], -edge[0], 0.0)
            length = math.hypot(normal[0], normal[1])
            if length > 0:
                normal = (normal[0] / length, normal[1] / length, 0.0)
            quad = (
                ((p0[0], p0[1], z_front), (0.0, 0.0)),
                ((p1[0], p1[1], z_front), (1.0, 0.0)),
                ((p1[0], p1[1], z_back), (1.0, 1.0)),
                ((p0[0], p0[1], z_back), (0.0, 1.0)),
            )
            for index in (0, 1, 2, 0, 2, 3):
                position, uv = quad[index]
                positions.append(position)
                normals.append(normal)
                uvs.append(uv)

        super().__init__({"position": positions, "normal": normals, "uv": uvs})
