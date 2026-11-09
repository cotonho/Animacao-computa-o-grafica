"""Base Aurora — disco voador + foguete.

Trabalho prático de Computação Gráfica (2026/02).

Execute:
    python main.py

Para gerar uma imagem sem interação:
    python main.py --screenshot screenshots/cena.png --time 10
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pygame
from OpenGL.GL import (
    GL_BACK,
    GL_PACK_ALIGNMENT,
    GL_RGBA,
    GL_UNSIGNED_BYTE,
    glFinish,
    glPixelStorei,
    glReadBuffer,
    glReadPixels,
)
from PIL import Image

from core.light import DirectionalLight, OrbitCamera
from core.object3d import Object3D
from core.renderer import Renderer
from core.scene import Scene
from scene.environment import build_environment
from scene.mission import DURATION, Mission
from scene.resources import Resources
from scene.rocket import Rocket
from scene.ufo import UFO

WINDOW_TITLE = (
    "Base Aurora | setas: orbitar | W/S: zoom | Espaco: pausar | "
    "R: reiniciar | F: sombras | B: bloom | C: camera | ESC: sair"
)


class Application:
    def __init__(self, width: int = 1600, height: int = 900, vsync: bool = True):
        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE
        )
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)

        flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE
        try:
            pygame.display.set_mode((width, height), flags, vsync=1 if vsync else 0)
        except pygame.error:
            pygame.display.set_mode((width, height), flags)

        pygame.display.set_caption(WINDOW_TITLE)
        self.width = width
        self.height = height
        self.clock = pygame.time.Clock()
        self.running = True
        self.paused = False
        self.time = 0.0
        self.fps = 0.0
        self._caption_timer = 0.0

        self.resources = Resources()
        self.root = Object3D("scene_root")
        self.environment = build_environment(self.resources)
        self.rocket = Rocket(self.resources, self.root)
        self.ufo = UFO(self.resources)
        self.root.add(self.environment.root, self.rocket.root, self.ufo.root)

        self.camera = OrbitCamera(
            target=(0.0, 4.0, 0.0),
            yaw=38.0,
            pitch=9.5,
            distance=23.0,
            fov_y=45.0,
        )
        self.light = DirectionalLight(
            direction=(-0.76, -0.40, 0.51),
            color=(1.0, 0.88, 0.70),
            ambient_sky=(0.24, 0.31, 0.42),
            ambient_ground=(0.34, 0.26, 0.19),
        )
        self.scene = Scene(self.root, self.camera, self.light)
        self.renderer = Renderer(self.width, self.height)
        self.mission = Mission(self.rocket, self.ufo, self.environment)
        self.mission.update(self.time)

    # ------------------------------------------------------------------
    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self.time = 0.0
                    self.paused = False
                elif event.key == pygame.K_f:
                    self.renderer.shadows_enabled = not self.renderer.shadows_enabled
                elif event.key == pygame.K_b:
                    self.renderer.bloom_enabled = not self.renderer.bloom_enabled
                elif event.key == pygame.K_c:
                    self.camera.reset()
            elif event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.w, event.h
                pygame.display.set_mode(
                    (self.width, self.height),
                    pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE,
                )
                self.renderer.resize(self.width, self.height)

    def _update_caption(self, dt: float) -> None:
        self._caption_timer += dt
        if self._caption_timer < 0.35:
            return
        self._caption_timer = 0.0
        state = "PAUSADO" if self.paused else "ANIMANDO"
        shadows = "sombras ON" if self.renderer.shadows_enabled else "sombras OFF"
        bloom = "bloom ON" if self.renderer.bloom_enabled else "bloom OFF"
        pygame.display.set_caption(
            f"Base Aurora | {state} | {shadows} | {bloom} | "
            f"{self.fps:4.0f} FPS | t={self.time:5.1f}s"
        )

    # ------------------------------------------------------------------
    def step(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        self.camera.handle_input(dt, keys)
        if not self.paused:
            self.time = (self.time + dt) % DURATION
        self.mission.update(self.time)
        aspect = self.width / max(1, self.height)
        self.camera.update(aspect)
        self.renderer.render(self.scene, self.camera)

    def run(self) -> None:
        while self.running:
            dt = min(self.clock.tick(60) / 1000.0, 0.05)
            self.fps = self.clock.get_fps()
            self._handle_events()
            self.step(dt)
            pygame.display.flip()
            self._update_caption(dt)
        pygame.quit()

    # ------------------------------------------------------------------
    def screenshot(self, path: str, time_seconds: float) -> None:
        self.time = time_seconds % DURATION
        self.mission.update(self.time)
        self.camera.update(self.width / max(1, self.height))
        # Dois frames garantem que o shadow map e os FBOs estejam prontos.
        self.renderer.render(self.scene, self.camera)
        self.renderer.render(self.scene, self.camera)
        glFinish()
        glReadBuffer(GL_BACK)
        glPixelStorei(GL_PACK_ALIGNMENT, 1)
        data = glReadPixels(0, 0, self.width, self.height, GL_RGBA, GL_UNSIGNED_BYTE)
        pixels = np.frombuffer(data, dtype=np.uint8).reshape(
            self.height, self.width, 4
        )[::-1]
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(pixels, mode="RGBA").convert("RGB").save(output)
        print(f"Screenshot salvo em {output} (t={time_seconds:.1f}s)")
        pygame.quit()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Base Aurora — cena 3D interativa")
    parser.add_argument("--width", type=int, default=1600)
    parser.add_argument("--height", type=int, default=900)
    parser.add_argument("--screenshot", type=str, default=None)
    parser.add_argument("--time", type=float, default=10.0)
    parser.add_argument("--no-bloom", action="store_true")
    parser.add_argument("--no-shadows", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    app = Application(args.width, args.height)
    if args.no_bloom:
        app.renderer.bloom_enabled = False
    if args.no_shadows:
        app.renderer.shadows_enabled = False
    if args.screenshot:
        app.screenshot(args.screenshot, args.time)
    else:
        app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
