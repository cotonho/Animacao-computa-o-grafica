"""Luz direcional e câmera em perspectiva com controle orbital por teclado."""

from __future__ import annotations

import math

import numpy as np
import pygame

from . import matrix
from .vector import Vec3


class DirectionalLight:
    def __init__(
        self,
        direction: tuple[float, float, float] = (-0.6, -0.55, 0.45),
        color: tuple[float, float, float] = (1.0, 0.9, 0.75),
        ambient_sky: tuple[float, float, float] = (0.20, 0.28, 0.38),
        ambient_ground: tuple[float, float, float] = (0.30, 0.24, 0.18),
    ):
        # direction é a direção de propagação da luz (do sol para a cena).
        self.direction = Vec3(*direction).normalized()
        self.color = color
        self.ambient_sky = ambient_sky
        self.ambient_ground = ambient_ground

    @property
    def direction_to_light(self) -> Vec3:
        return -self.direction

    def view_projection(
        self,
        center: tuple[float, float, float] = (0.0, 2.0, 0.0),
        radius: float = 18.0,
        distance: float = 32.0,
    ) -> np.ndarray:
        center_vec = np.asarray(center, dtype=np.float64)
        eye = center_vec - self.direction.array * distance
        up = np.array([0.0, 1.0, 0.0])
        view = matrix.look_at(eye, center_vec, up)
        projection = matrix.orthographic(
            -radius, radius, -radius, radius, 0.1, distance * 2.0
        )
        return projection @ view


class OrbitCamera:
    """Câmera em perspectiva orbitando um ponto de interesse.

    Setas: yaw/pitch. W/S ou +/-: distância. A orientação é sempre recalculada
    a partir de yaw, pitch e distância, então o controle é independente da
    taxa de quadros.
    """

    def __init__(
        self,
        target: tuple[float, float, float] = (0.0, 3.0, 0.0),
        yaw: float = 38.0,
        pitch: float = 17.0,
        distance: float = 21.0,
        fov_y: float = 45.0,
        near: float = 0.1,
        far: float = 200.0,
    ):
        self.target = Vec3(*target)
        self.yaw = yaw
        self.pitch = pitch
        self.distance = distance
        self.fov_y = fov_y
        self.near = near
        self.far = far
        self.eye = Vec3()
        self.view = matrix.identity()
        self.projection = matrix.identity()
        self._update_eye()

    def _update_eye(self) -> None:
        yaw = math.radians(self.yaw)
        pitch = math.radians(self.pitch)
        horizontal = math.cos(pitch) * self.distance
        self.eye = Vec3(
            self.target.x + horizontal * math.sin(yaw),
            self.target.y + math.sin(pitch) * self.distance,
            self.target.z + horizontal * math.cos(yaw),
        )

    def handle_input(self, dt: float, keys) -> None:
        speed = 65.0
        if keys[pygame.K_LEFT]:
            self.yaw -= speed * dt
        if keys[pygame.K_RIGHT]:
            self.yaw += speed * dt
        if keys[pygame.K_UP]:
            self.pitch = min(80.0, self.pitch + 45.0 * dt)
        if keys[pygame.K_DOWN]:
            self.pitch = max(1.0, self.pitch - 45.0 * dt)
        if keys[pygame.K_w] or keys[pygame.K_PLUS] or keys[pygame.K_KP_PLUS]:
            self.distance = max(7.0, self.distance - 9.0 * dt)
        if keys[pygame.K_s] or keys[pygame.K_MINUS] or keys[pygame.K_KP_MINUS]:
            self.distance = min(55.0, self.distance + 9.0 * dt)
        self._update_eye()

    def reset(self) -> None:
        self.target = Vec3(0.0, 4.0, 0.0)
        self.yaw = 38.0
        self.pitch = 9.5
        self.distance = 23.0
        self._update_eye()

    def update(self, aspect: float) -> None:
        self.view = matrix.look_at(self.eye.array, self.target.array, (0.0, 1.0, 0.0))
        self.projection = matrix.perspective(self.fov_y, aspect, self.near, self.far)
