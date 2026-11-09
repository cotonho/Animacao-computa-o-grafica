"""Foguete de brinquedo: corpo, aletas, janela, motor e fumaça."""

from __future__ import annotations

import math
import random

from core.geometry import (
    ConeGeometry,
    CylinderGeometry,
    PrismGeometry,
    SphereGeometry,
    TorusGeometry,
)
from core.material import Material
from core.mesh import Mesh
from core.object3d import Object3D
from core.vector import Vec3

from .constants import ROCKET_BASE_Y
from .resources import Resources


class Rocket:
    def __init__(self, resources: Resources, effects_root: Object3D):
        self.resources = resources
        self.root = Object3D("rocket")
        self.root.translation = Vec3(0.0, ROCKET_BASE_Y, 0.0)

        self.body = Object3D("rocket_body_group")
        self.root.add(self.body)

        self._build_hull()
        self._build_fins()
        self._build_porthole()
        self._build_engine()
        self._build_smoke(effects_root)

    # ------------------------------------------------------------------
    def _build_hull(self) -> None:
        hull = Object3D("rocket_hull")
        hull.translation.y = 2.0
        hull.mesh = Mesh(
            CylinderGeometry(0.52, 0.60, 3.2, 32, 1),
            self.resources.rocket_body(),
        )
        self.body.add(hull)

        nose_material = Material(
            color=(0.78, 0.08, 0.10),
            specular=(0.55, 0.35, 0.30),
            shininess=55.0,
            ambient=0.95,
        )
        nose = Object3D("rocket_nose")
        nose.translation.y = 3.60
        nose.mesh = Mesh(
            ConeGeometry(0.54, 1.15, 32, cap=True, origin="base"),
            nose_material,
        )
        self.body.add(nose)

        tip = Object3D("rocket_tip")
        tip.translation.y = 4.72
        tip.mesh = Mesh(SphereGeometry(0.075, 12, 8), self.resources.metal((0.9, 0.9, 0.9)))
        self.body.add(tip)

        # anel de reforço na base do nariz
        ring = Object3D("rocket_nose_ring")
        ring.translation.y = 3.60
        ring.mesh = Mesh(TorusGeometry(0.53, 0.045, 32, 10), self.resources.dark_metal())
        self.body.add(ring)

    def _build_fins(self) -> None:
        fin_material = Material(
            color=(0.10, 0.23, 0.62),
            specular=(0.35, 0.40, 0.55),
            shininess=45.0,
            ambient=0.95,
        )
        fin_geometry = PrismGeometry([(0.0, 0.0), (0.0, 0.98), (0.82, 0.0)], depth=0.09)
        for index in range(4):
            fin_pivot = Object3D(f"rocket_fin_{index}")
            fin_pivot.translation = Vec3(0.0, 0.55, 0.0)
            fin_pivot.rotation.y = index * 90.0
            self.body.add(fin_pivot)

            fin = Object3D("fin_blade")
            fin.translation.x = 0.50
            fin.mesh = Mesh(fin_geometry, fin_material)
            fin_pivot.add(fin)

    def _build_porthole(self) -> None:
        ring = Object3D("rocket_porthole_ring")
        ring.translation = Vec3(0.0, 2.78, 0.51)
        ring.rotation.x = 90.0
        ring.mesh = Mesh(TorusGeometry(0.27, 0.065, 28, 10), self.resources.dark_metal())
        self.body.add(ring)

        glass = Object3D("rocket_porthole_glass")
        glass.translation = Vec3(0.0, 2.78, 0.48)
        glass.scale = Vec3(1.0, 1.0, 0.35)
        glass.mesh = Mesh(SphereGeometry(0.255, 24, 14), self.resources.glass())
        self.body.add(glass)

    def _build_engine(self) -> None:
        nozzle = Object3D("rocket_nozzle")
        nozzle.translation.y = 0.25
        nozzle.mesh = Mesh(CylinderGeometry(0.28, 0.47, 0.5, 28), self.resources.dark_metal())
        self.body.add(nozzle)

        self.flame_outer = Object3D("rocket_flame_outer")
        self.flame_outer.translation.y = 0.02
        self.flame_outer.rotation.x = 180.0
        self.flame_outer.mesh = Mesh(
            ConeGeometry(0.48, 2.2, 24, cap=False, origin="base"),
            self.resources.flame((1.0, 0.36, 0.04), opacity=0.72),
        )
        self.body.add(self.flame_outer)

        self.flame_inner = Object3D("rocket_flame_inner")
        self.flame_inner.translation.y = 0.02
        self.flame_inner.rotation.x = 180.0
        self.flame_inner.mesh = Mesh(
            ConeGeometry(0.26, 1.35, 20, cap=False, origin="base"),
            self.resources.flame((1.0, 0.85, 0.35), opacity=0.9),
        )
        self.body.add(self.flame_inner)

        self.engine_glow = Object3D("rocket_engine_glow")
        self.engine_glow.translation.y = 0.02
        self.engine_glow.mesh = Mesh(SphereGeometry(0.33, 20, 12), self.resources.light((1.0, 0.42, 0.06)))
        self.body.add(self.engine_glow)

        self.set_engine(False, 0.0, 0.0)

    # ------------------------------------------------------------------
    def _build_smoke(self, effects_root: Object3D) -> None:
        self.smoke_puffs: list[dict] = []
        geometry = SphereGeometry(1.0, 10, 7)
        rng = random.Random(31)
        for index in range(18):
            material = self.resources.smoke(0.0)
            node = Object3D(f"smoke_{index}")
            node.mesh = Mesh(geometry, material)
            node.visible = False
            effects_root.add(node)

            angle = rng.uniform(0.0, math.tau)
            radius = rng.uniform(0.45, 1.25)
            self.smoke_puffs.append(
                {
                    "node": node,
                    "material": material,
                    "spawn": rng.uniform(0.0, 2.4),
                    "life": rng.uniform(2.8, 4.6),
                    "base": Vec3(
                        math.cos(angle) * radius,
                        0.55 + rng.uniform(0.0, 0.25),
                        math.sin(angle) * radius,
                    ),
                    "drift": Vec3(
                        math.cos(angle) * rng.uniform(0.35, 0.95),
                        rng.uniform(0.55, 1.15),
                        math.sin(angle) * rng.uniform(0.35, 0.95),
                    ),
                    "size": rng.uniform(0.35, 0.75),
                }
            )

    def update_smoke(self, time: float, ignition_time: float) -> None:
        for puff in self.smoke_puffs:
            age = time - (ignition_time + puff["spawn"])
            life = puff["life"]
            if 0.0 <= age < life:
                node = puff["node"]
                node.visible = True
                growth = puff["size"] * (0.45 + age * 0.72)
                node.scale = Vec3(growth, growth * 0.85, growth)
                base = puff["base"]
                drift = puff["drift"]
                node.translation = Vec3(
                    base.x + drift.x * age,
                    base.y + drift.y * age,
                    base.z + drift.z * age,
                )
                fade = max(0.0, 1.0 - age / life)
                puff["material"].opacity = 0.34 * (fade ** 1.4)
            else:
                puff["node"].visible = False

    # ------------------------------------------------------------------
    def set_engine(self, active: bool, time: float, power: float) -> None:
        self.flame_outer.visible = active
        self.flame_inner.visible = active
        self.engine_glow.visible = active
        if not active:
            return

        flicker = 0.92 + 0.08 * math.sin(time * 47.0) + 0.04 * math.sin(time * 83.0 + 1.7)
        outer = max(0.15, power) * flicker
        inner = max(0.12, power) * (0.95 + 0.05 * math.sin(time * 61.0 + 0.6))
        self.flame_outer.scale = Vec3(0.85 + 0.2 * outer, 0.55 + 0.9 * outer, 0.85 + 0.2 * outer)
        self.flame_inner.scale = Vec3(0.9 + 0.1 * inner, 0.55 + 0.8 * inner, 0.9 + 0.1 * inner)
        self.flame_outer.mesh.material.opacity = 0.72 * min(1.0, outer)
        self.flame_inner.mesh.material.opacity = 0.9 * min(1.0, inner)
        glow_scale = 0.85 + 0.25 * flicker
        self.engine_glow.scale = Vec3(glow_scale, glow_scale, glow_scale)
