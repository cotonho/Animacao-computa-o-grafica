"""Ambiente: base de testes no deserto, plataforma, torre e paisagem."""

from __future__ import annotations

import math
import random

from core.geometry import BoxGeometry, CylinderGeometry, PlaneGeometry, SphereGeometry
from core.material import Material
from core.mesh import Mesh
from core.object3d import Object3D
from core.vector import Vec3

from .constants import PAD_SIZE, PAD_TOP, ROCKET_BASE_Y
from .resources import Resources


class Environment:
    def __init__(self, root: Object3D, clamp_arms: list[Object3D], pad_lights: list[Material],
                 beacon: Material, bunker_light: Material):
        self.root = root
        self.clamp_arms = clamp_arms
        self.pad_lights = pad_lights
        self.beacon = beacon
        self.bunker_light = bunker_light


def build_environment(resources: Resources) -> Environment:
    root = Object3D("environment")

    _build_ground(root, resources)
    pad_lights = _build_pad(root, resources)
    clamp_arms = _build_clamps(root, resources)
    beacon = _build_tower(root, resources)
    bunker_light = _build_bunker(root, resources)
    _build_landscape(root, resources)

    # O beacon da torre e a janela do bunker são devolvidos para a missão
    # poder animar as luzes durante a contagem.
    return Environment(root, clamp_arms, pad_lights, beacon, bunker_light)


def _build_ground(root: Object3D, resources: Resources) -> None:
    ground = Object3D("ground")
    ground.mesh = Mesh(PlaneGeometry(100.0, 100.0, 1, 1, uv_repeat=(20.0, 20.0)), resources.sand())
    root.add(ground)


def _build_pad(root: Object3D, resources: Resources) -> list[Material]:
    pad = Object3D("launch_pad")
    pad.translation.y = PAD_TOP / 2.0
    pad.mesh = Mesh(BoxGeometry(PAD_SIZE, PAD_TOP, PAD_SIZE), resources.pad())
    root.add(pad)

    # Base metálica sob o foguete.
    mount = Object3D("launch_mount")
    mount.translation.y = PAD_TOP + 0.06
    mount.mesh = Mesh(CylinderGeometry(0.78, 0.88, 0.18, 32), resources.dark_metal())
    root.add(mount)

    # Luzes de balizamento nos cantos da plataforma.
    light_geometry = SphereGeometry(0.075, 12, 8)
    light_materials: list[Material] = []
    for index, (x, z) in enumerate(
        ((-3.6, -3.6), (3.6, -3.6), (3.6, 3.6), (-3.6, 3.6),
         (0.0, -4.0), (4.0, 0.0), (0.0, 4.0), (-4.0, 0.0))
    ):
        material = resources.light((1.0, 0.45, 0.08))
        light_materials.append(material)
        node = Object3D(f"pad_light_{index}")
        node.translation = Vec3(x, PAD_TOP + 0.08, z)
        node.mesh = Mesh(light_geometry, material)
        root.add(node)

    # Postes baixos de proteção.
    post_geometry = BoxGeometry(0.12, 0.5, 0.12)
    for x, z in ((-4.2, -4.2), (4.2, -4.2), (4.2, 4.2), (-4.2, 4.2)):
        post = Object3D("pad_post")
        post.translation = Vec3(x, PAD_TOP + 0.25, z)
        post.mesh = Mesh(post_geometry, resources.metal((0.55, 0.58, 0.62)))
        root.add(post)

    return light_materials


def _build_clamps(root: Object3D, resources: Resources) -> list[Object3D]:
    """Quatro braços que se afastam radialmente no momento do lançamento."""
    arm_geometry = BoxGeometry(0.85, 0.16, 0.22)
    pad_geometry = BoxGeometry(0.22, 0.58, 0.32)
    base_geometry = BoxGeometry(0.38, 0.22, 0.38)
    arm_material = resources.metal((0.95, 0.62, 0.18))
    pad_material = resources.dark_metal()

    arms: list[Object3D] = []
    for index in range(4):
        clamp = Object3D(f"clamp_{index}")
        clamp.translation = Vec3(0.0, ROCKET_BASE_Y, 0.0)
        clamp.rotation.y = index * 90.0
        root.add(clamp)

        base = Object3D("clamp_base")
        base.translation = Vec3(1.22, 0.0, 0.0)
        base.mesh = Mesh(base_geometry, pad_material)
        clamp.add(base)

        arm = Object3D(f"clamp_arm_{index}")
        arm.translation = Vec3(0.95, 0.0, 0.0)
        clamp.add(arm)
        arms.append(arm)

        arm_mesh = Object3D("clamp_bar")
        arm_mesh.translation = Vec3(0.0, 0.08, 0.0)
        arm_mesh.mesh = Mesh(arm_geometry, arm_material)
        arm.add(arm_mesh)

        pad_mesh = Object3D("clamp_pad")
        pad_mesh.translation = Vec3(-0.34, 0.38, 0.0)
        pad_mesh.mesh = Mesh(pad_geometry, pad_material)
        arm.add(pad_mesh)

    return arms


def _build_tower(root: Object3D, resources: Resources) -> Material:
    tower = Object3D("service_tower")
    tower.translation = Vec3(-4.4, PAD_TOP, -3.2)
    root.add(tower)

    leg_geometry = BoxGeometry(0.16, 7.4, 0.16)
    metal = resources.metal((0.62, 0.66, 0.72))
    for x, z in ((-0.75, -0.75), (0.75, -0.75), (0.75, 0.75), (-0.75, 0.75)):
        leg = Object3D("tower_leg")
        leg.translation = Vec3(x, 3.7, z)
        leg.mesh = Mesh(leg_geometry, metal)
        tower.add(leg)

    cross_x = BoxGeometry(1.65, 0.11, 0.11)
    cross_z = BoxGeometry(0.11, 0.11, 1.65)
    for level in range(1, 7):
        y = level * 1.05
        beam_x = Object3D("tower_beam_x")
        beam_x.translation = Vec3(0.0, y, 0.75)
        beam_x.mesh = Mesh(cross_x, metal)
        tower.add(beam_x)
        beam_z = Object3D("tower_beam_z")
        beam_z.translation = Vec3(0.75, y, 0.0)
        beam_z.mesh = Mesh(cross_z, metal)
        tower.add(beam_z)

    # braço de serviço apontando para a plataforma
    service_arm = Object3D("service_arm")
    service_arm.translation = Vec3(1.8, 6.5, 0.0)
    service_arm.mesh = Mesh(BoxGeometry(2.8, 0.16, 0.22), metal)
    tower.add(service_arm)

    platform = Object3D("tower_platform")
    platform.translation = Vec3(0.0, 7.45, 0.0)
    platform.mesh = Mesh(BoxGeometry(2.1, 0.16, 2.1), metal)
    tower.add(platform)

    antenna = Object3D("tower_antenna")
    antenna.translation = Vec3(0.0, 8.1, 0.0)
    antenna.mesh = Mesh(CylinderGeometry(0.05, 0.05, 1.3, 12), resources.dark_metal())
    tower.add(antenna)

    beacon = Object3D("tower_beacon")
    beacon.translation = Vec3(0.0, 8.85, 0.0)
    beacon_material = resources.light((1.0, 0.12, 0.08))
    beacon.mesh = Mesh(SphereGeometry(0.14, 16, 10), beacon_material)
    tower.add(beacon)
    return beacon_material


def _build_bunker(root: Object3D, resources: Resources) -> Material:
    bunker = Object3D("control_bunker")
    bunker.translation = Vec3(-9.0, 0.0, -7.5)
    root.add(bunker)

    concrete = resources.metal((0.72, 0.72, 0.70))
    body = Object3D("bunker_body")
    body.translation.y = 0.75
    body.mesh = Mesh(BoxGeometry(3.4, 1.5, 2.6), concrete)
    bunker.add(body)

    roof = Object3D("bunker_roof")
    roof.translation.y = 1.58
    roof.mesh = Mesh(BoxGeometry(3.65, 0.16, 2.85), resources.dark_metal())
    bunker.add(roof)

    door = Object3D("bunker_door")
    door.translation = Vec3(0.8, 0.55, 1.32)
    door.mesh = Mesh(BoxGeometry(0.8, 1.1, 0.08), resources.dark_metal())
    bunker.add(door)

    window_material = resources.light((0.15, 0.75, 1.0))
    window = Object3D("bunker_window")
    window.translation = Vec3(-0.75, 0.9, 1.33)
    window.mesh = Mesh(BoxGeometry(1.3, 0.24, 0.05), window_material)
    bunker.add(window)

    antenna = Object3D("bunker_antenna")
    antenna.translation = Vec3(1.3, 2.05, 0.0)
    antenna.mesh = Mesh(CylinderGeometry(0.04, 0.04, 1.1, 10), resources.dark_metal())
    bunker.add(antenna)

    dish = Object3D("bunker_dish")
    dish.translation = Vec3(1.3, 2.65, 0.0)
    dish.rotation.z = 25.0
    dish.mesh = Mesh(CylinderGeometry(0.32, 0.1, 0.12, 20), resources.metal((0.8, 0.8, 0.8)))
    bunker.add(dish)

    return window_material


def _build_landscape(root: Object3D, resources: Resources) -> None:
    rng = random.Random(7)
    rock_geometry = SphereGeometry(1.0, 8, 6)
    rock_material = Material(
        color=(0.42, 0.34, 0.26),
        specular=(0.04, 0.04, 0.04),
        shininess=8.0,
        ambient=0.95,
    )
    for index in range(15):
        angle = rng.uniform(0.0, math.tau)
        distance = rng.uniform(8.5, 25.0)
        scale_x = rng.uniform(0.3, 1.3)
        scale_y = rng.uniform(0.2, 0.8)
        scale_z = rng.uniform(0.3, 1.2)
        rock = Object3D(f"rock_{index}")
        rock.translation = Vec3(
            math.cos(angle) * distance,
            scale_y * 0.35,
            math.sin(angle) * distance,
        )
        rock.rotation = Vec3(
            rng.uniform(0, 360), rng.uniform(0, 360), rng.uniform(0, 360)
        )
        rock.scale = Vec3(scale_x, scale_y, scale_z)
        rock.mesh = Mesh(rock_geometry, rock_material)
        root.add(rock)

    # mesetas distantes
    mesa_material = Material(
        color=(0.40, 0.27, 0.21),
        specular=(0.02, 0.02, 0.02),
        shininess=4.0,
        ambient=0.95,
    )
    for index, (angle, distance, radius, height) in enumerate(
        (
            (0.25, 38.0, 7.0, 7.0),
            (1.25, 46.0, 9.0, 9.0),
            (2.35, 41.0, 6.0, 5.5),
            (3.55, 44.0, 8.0, 8.0),
            (4.65, 39.0, 5.5, 6.5),
            (5.55, 48.0, 10.0, 7.0),
        )
    ):
        mesa = Object3D(f"mesa_{index}")
        mesa.translation = Vec3(
            math.cos(angle) * distance, height / 2.0 - 0.3, math.sin(angle) * distance
        )
        mesa.rotation.y = rng.uniform(0, 360)
        mesa.mesh = Mesh(
            CylinderGeometry(radius * 0.72, radius, height, 10, 1),
            mesa_material,
        )
        root.add(mesa)

    _build_cactus(root, resources, (-13.0, 7.5), 1.0)
    _build_cactus(root, resources, (15.0, -9.0), 0.85)
    _build_cactus(root, resources, (-19.0, -13.0), 1.15)


def _build_cactus(root: Object3D, resources: Resources, position: tuple[float, float], scale: float) -> None:
    green = Material(
        color=(0.16, 0.32, 0.15),
        specular=(0.08, 0.10, 0.08),
        shininess=12.0,
        ambient=0.95,
    )
    cactus = Object3D("cactus")
    cactus.translation = Vec3(position[0], 0.0, position[1])
    cactus.scale = Vec3(scale, scale, scale)
    root.add(cactus)

    trunk = Object3D("cactus_trunk")
    trunk.translation.y = 1.1
    trunk.mesh = Mesh(CylinderGeometry(0.22, 0.26, 2.2, 10), green)
    cactus.add(trunk)

    top = Object3D("cactus_top")
    top.translation.y = 2.2
    top.mesh = Mesh(SphereGeometry(0.23, 10, 8), green)
    cactus.add(top)

    for side, height in ((1, 1.25), (-1, 1.6)):
        arm = Object3D("cactus_arm")
        arm.translation = Vec3(side * 0.38, height, 0.0)
        arm.rotation.z = 90.0
        arm.mesh = Mesh(CylinderGeometry(0.12, 0.13, 0.75, 8), green)
        cactus.add(arm)
        tip = Object3D("cactus_arm_top")
        tip.translation = Vec3(side * 0.76, height, 0.0)
        tip.mesh = Mesh(SphereGeometry(0.13, 8, 6), green)
        cactus.add(tip)

