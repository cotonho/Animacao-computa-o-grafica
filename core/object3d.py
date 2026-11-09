"""Nó da cena com transformações hierárquicas (translação/rotação/escala)."""

from __future__ import annotations

import numpy as np

from . import matrix
from .mesh import Mesh
from .vector import Vec3


class Object3D:
    def __init__(self, name: str = "object"):
        self.name = name
        self.translation = Vec3()
        self.rotation = Vec3()
        self.scale = Vec3(1.0, 1.0, 1.0)
        self.matrix = matrix.identity()
        self.mesh: Mesh | None = None
        self.children: list[Object3D] = []
        self.parent: Object3D | None = None
        self.visible = True

    # ------------------------------------------------------------------
    def add(self, *children: "Object3D") -> "Object3D":
        for child in children:
            child.parent = self
            self.children.append(child)
        return self

    def local_matrix(self) -> np.ndarray:
        return matrix.compose(
            self.translation.as_tuple(),
            self.rotation.as_tuple(),
            self.scale.as_tuple(),
        )

    def update_matrix(self, parent_matrix: np.ndarray | None = None) -> None:
        local = self.local_matrix()
        self.matrix = local if parent_matrix is None else parent_matrix @ local
        for child in self.children:
            child.update_matrix(self.matrix)

    def world_position(self) -> np.ndarray:
        return matrix.transform_point(self.matrix, (0.0, 0.0, 0.0))

    def set_mesh(self, mesh: Mesh) -> "Object3D":
        self.mesh = mesh
        return self

    # ------------------------------------------------------------------
    def find(self, name: str) -> "Object3D | None":
        if self.name == name:
            return self
        for child in self.children:
            found = child.find(name)
            if found is not None:
                return found
        return None
