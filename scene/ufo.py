"""Disco voador: casco, anel giratório, luzes, cúpula e feixe de inspeção."""

from __future__ import annotations

import math

from core.geometry import (
    BoxGeometry,
    ConeGeometry,
    CylinderGeometry,
    EllipsoidGeometry,
    SphereGeometry,
    TorusGeometry,
)
from core.material import Material
from core.mesh import Mesh
from core.object3d import Object3D
from core.vector import Vec3

from .resources import Resources


class UFO:
    def __init__(self, resources: Resources):
        self.resources = resources
        self.root = Object3D("ufo")
        self.body = Object3D("ufo_body")
        self.root.add(self.body)

        self._build_hull()
        self._build_rotating_ring()
        self._build_cockpit()
        self._build_beam()

        self.signal_material = resources.light((0.25, 1.0, 0.45))
        signal = Object3D("ufo_signal_light")
        signal.translation = Vec3(0.0, 1.32, 0.0)
        signal.mesh = Mesh(SphereGeometry(0.11, 16, 10), self.signal_material)
        self.body.add(signal)

    # ------------------------------------------------------------------
    def _build_hull(self) -> None:
        lower = Object3D("ufo_lower_hull")
        lower.mesh = Mesh(EllipsoidGeometry(2.20, 0.48, 2.20, 44, 22), self.resources.ufo_hull())
        self.body.add(lower)

        upper = Object3D("ufo_upper_hull")
        upper.translation.y = 0.20
        upper.mesh = Mesh(EllipsoidGeometry(1.72, 0.60, 1.72, 40, 20), self.resources.ufo_hull())
        self.body.add(upper)

        equator = Object3D("ufo_equator")
        equator.translation.y = 0.02
        equator.mesh = Mesh(TorusGeometry(2.10, 0.10, 48, 12), self.resources.dark_metal())
        self.body.add(equator)

        emitter = Object3D("ufo_emitter")
        emitter.translation.y = -0.47
        emitter.mesh = Mesh(CylinderGeometry(0.22, 0.36, 0.22, 24), self.resources.dark_metal())
        self.body.add(emitter)

        emitter_light = Object3D("ufo_emitter_light")
        emitter_light.translation.y = -0.60
        emitter_light.mesh = Mesh(
            CylinderGeometry(0.16, 0.24, 0.08, 24),
            self.resources.light((0.15, 0.95, 0.75)),
        )
        self.body.add(emitter_light)

    def _build_rotating_ring(self) -> None:
        self.ring = Object3D("ufo_outer_ring")
        self.ring.translation.y = -0.05
        self.body.add(self.ring)

        ring_mesh = Object3D("ufo_ring_torus")
        ring_mesh.mesh = Mesh(TorusGeometry(2.42, 0.145, 64, 16), self.resources.dark_metal())
        self.ring.add(ring_mesh)

        self.light_materials: list[Material] = []
        self.light_colors: list[tuple[float, float, float]] = []
        light_geometry = SphereGeometry(0.105, 14, 10)
        for index in range(10):
            angle = math.tau * index / 10.0
            if index % 2 == 0:
                color = (0.10, 0.95, 1.00)
            else:
                color = (0.25, 1.00, 0.45)
            material = self.resources.light(color)
            self.light_materials.append(material)
            self.light_colors.append(color)

            light = Object3D(f"ufo_ring_light_{index}")
            light.translation = Vec3(
                math.cos(angle) * 2.42, 0.09, math.sin(angle) * 2.42
            )
            light.mesh = Mesh(light_geometry, material)
            self.ring.add(light)

        # painéis que tornam a rotação do anel perceptível mesmo de longe
        panel_geometry = BoxGeometry(0.42, 0.07, 0.16)
        panel_material = self.resources.metal((0.75, 0.62, 0.30))
        for index in range(4):
            angle = math.tau * index / 4.0 + math.pi / 4.0
            panel = Object3D(f"ufo_ring_panel_{index}")
            panel.translation = Vec3(
                math.cos(angle) * 2.36, -0.02, math.sin(angle) * 2.36
            )
            panel.rotation.y = -math.degrees(angle)
            panel.mesh = Mesh(panel_geometry, panel_material)
            self.ring.add(panel)

        self.inner_ring = Object3D("ufo_inner_ring")
        self.inner_ring.translation.y = -0.28
        self.body.add(self.inner_ring)
        inner = Object3D("ufo_inner_ring_torus")
        inner.mesh = Mesh(TorusGeometry(1.18, 0.055, 48, 10), self.resources.metal((0.35, 0.55, 0.65)))
        self.inner_ring.add(inner)

    def _build_cockpit(self) -> None:
        base = Object3D("ufo_cockpit_base")
        base.translation.y = 0.53
        base.mesh = Mesh(TorusGeometry(0.88, 0.065, 36, 10), self.resources.dark_metal())
        self.body.add(base)

        dome = Object3D("ufo_cockpit")
        dome.translation.y = 0.60
        dome.scale = Vec3(1.0, 0.78, 1.0)
        dome.mesh = Mesh(SphereGeometry(0.86, 32, 18), self.resources.glass())
        self.body.add(dome)

        antenna = Object3D("ufo_antenna")
        antenna.translation.y = 1.02
        antenna.mesh = Mesh(CylinderGeometry(0.025, 0.025, 0.42, 8), self.resources.dark_metal())
        self.body.add(antenna)

    def _build_beam(self) -> None:
        self.beam_pivot = Object3D("ufo_beam_pivot")
        self.beam_pivot.translation = Vec3(0.0, -0.62, 0.0)
        self.body.add(self.beam_pivot)

        self.beam = Object3D("ufo_beam")
        self.beam.mesh = Mesh(
            ConeGeometry(1.20, 1.0, 32, cap=False, origin="apex"),
            self.resources.beam(),
        )
        self.beam.visible = False
        self.beam_pivot.add(self.beam)

    # ------------------------------------------------------------------
    def update_animation(self, time: float, bank_degrees: float = 0.0,
                         tilt_degrees: float = 0.0) -> None:
        self.body.translation.y = 0.10 * math.sin(time * 2.2)
        self.body.rotation.z = bank_degrees + 0.025 * math.sin(time * 1.6)
        self.body.rotation.x = tilt_degrees + 0.020 * math.sin(time * 1.9)

        self.ring.rotation.y = time * 110.0
        self.inner_ring.rotation.y = -time * 165.0

        for index, material in enumerate(self.light_materials):
            pulse = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(time * 5.0 + index * 0.65))
            color = self.light_colors[index]
            material.emissive = (color[0] * pulse, color[1] * pulse, color[2] * pulse)

    def set_beam(self, active: bool, target_world: Vec3, time: float = 0.0) -> None:
        self.beam.visible = active
        if not active:
            return

        dx = target_world.x - self.root.translation.x
        dz = target_world.z - self.root.translation.z
        horizontal = math.hypot(dx, dz)
        vertical = max(
            0.2,
            self.root.translation.y + self.body.translation.y - 0.62 - target_world.y,
        )
        angle = math.degrees(math.atan2(horizontal, vertical))
        length = math.hypot(horizontal, vertical)

        self.beam_pivot.rotation.x = -angle
        self.beam.scale = Vec3(1.0, length, 1.0)
        self.beam.mesh.material.opacity = 0.075 + 0.025 * (0.5 + 0.5 * math.sin(time * 9.0))

    def set_signal(self, intensity: float) -> None:
        self.signal_material.emissive = (
            0.25 * intensity,
            1.0 * intensity,
            0.45 * intensity,
        )
