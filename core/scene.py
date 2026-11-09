"""Cena: raiz hierárquica, câmera e luz direcional."""

from __future__ import annotations

from .light import DirectionalLight, OrbitCamera
from .object3d import Object3D


class Scene:
    def __init__(
        self,
        root: Object3D,
        camera: OrbitCamera,
        light: DirectionalLight,
    ):
        self.root = root
        self.camera = camera
        self.light = light

    def update_matrices(self) -> None:
        self.root.update_matrix()
