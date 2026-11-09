"""Recursos compartilhados: texturas e materiais base."""

from __future__ import annotations

from core.material import Material
from core.texture import Texture
from core.utils import texture_path


class Resources:
    def __init__(self):
        self.sand_texture = Texture(texture_path("sand.png"))
        self.metal_texture = Texture(texture_path("metal_panels.png"))
        self.rocket_texture = Texture(texture_path("rocket_body.png"))
        self.pad_texture = Texture(texture_path("pad.png"))
        self.ufo_texture = Texture(texture_path("ufo_hull.png"))

    # ------------------------------------------------------------------
    def sand(self) -> Material:
        return Material(
            color=(1.0, 0.93, 0.82),
            specular=(0.04, 0.04, 0.04),
            shininess=8.0,
            ambient=0.95,
            texture=self.sand_texture,
        )

    def pad(self) -> Material:
        return Material(
            color=(1.0, 1.0, 1.0),
            specular=(0.22, 0.22, 0.22),
            shininess=28.0,
            ambient=0.95,
            texture=self.pad_texture,
        )

    def metal(self, tint=(0.72, 0.78, 0.88)) -> Material:
        return Material(
            color=tint,
            specular=(0.75, 0.78, 0.82),
            shininess=70.0,
            ambient=0.9,
            texture=self.metal_texture,
        )

    def dark_metal(self) -> Material:
        return Material(
            color=(0.11, 0.13, 0.17),
            specular=(0.55, 0.6, 0.7),
            shininess=55.0,
            ambient=0.8,
        )

    def rocket_body(self) -> Material:
        return Material(
            color=(1.0, 1.0, 1.0),
            specular=(0.45, 0.45, 0.45),
            shininess=45.0,
            ambient=0.95,
            texture=self.rocket_texture,
        )

    def ufo_hull(self) -> Material:
        return Material(
            color=(0.85, 0.9, 1.0),
            specular=(0.95, 0.95, 1.0),
            shininess=95.0,
            ambient=0.95,
            texture=self.ufo_texture,
        )

    def glass(self) -> Material:
        return Material(
            color=(0.06, 0.32, 0.42),
            specular=(1.0, 1.0, 1.0),
            shininess=140.0,
            ambient=0.9,
            emissive=(0.03, 0.30, 0.42),
        )

    def light(self, color=(0.2, 1.0, 0.75)) -> Material:
        return Material(
            color=(0.02, 0.02, 0.02),
            specular=(0.0, 0.0, 0.0),
            shininess=1.0,
            ambient=1.0,
            emissive=color,
            unlit=True,
        )

    def flame(self, color=(1.0, 0.42, 0.06), opacity=0.75) -> Material:
        return Material(
            color=(0.0, 0.0, 0.0),
            emissive=color,
            unlit=True,
            opacity=opacity,
            transparent=True,
            additive=True,
            double_sided=True,
            cast_shadow=False,
            receive_shadow=False,
        )

    def beam(self, color=(0.12, 0.95, 0.60), opacity=0.10) -> Material:
        return Material(
            color=(0.0, 0.0, 0.0),
            emissive=color,
            unlit=True,
            opacity=opacity,
            transparent=True,
            additive=True,
            double_sided=True,
            cast_shadow=False,
            receive_shadow=False,
        )

    def smoke(self, opacity=0.35) -> Material:
        return Material(
            color=(0.55, 0.53, 0.50),
            specular=(0.0, 0.0, 0.0),
            shininess=1.0,
            ambient=1.0,
            opacity=opacity,
            transparent=True,
            additive=False,
            cast_shadow=False,
            receive_shadow=False,
        )
