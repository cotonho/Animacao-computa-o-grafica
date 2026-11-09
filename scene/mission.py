"""Coreografia da missão.

A interação é uma sequência de etapas controlada pelo tempo decorrido:

  0.0 -  6.0  aproximação do disco voador
  6.0 - 14.0  inspeção orbital com feixe de varredura
 14.0 - 16.5  sinal verde e abertura dos suportes
 16.5 - 17.5  ignição do motor
 17.5 - 21.5  subida do foguete, acompanhada pelo disco
 21.5 - 23.0  pairar no alto
 23.0 - 26.0  descida e pouso
 26.3 - 27.5  fechamento dos suportes
 27.5 - 30.5  retorno do disco à posição inicial
 30.5 - 32.0  pausa e reinício do ciclo

Todos os movimentos usam funções de interpolação suaves e são recalculados
a partir de ``time``; portanto, a velocidade não depende da taxa de quadros.
"""

from __future__ import annotations

import math

from core.vector import Vec3

from .constants import ROCKET_BASE_Y
from .environment import Environment
from .rocket import Rocket
from .ufo import UFO

DURATION = 32.0

APPROACH_END = 6.0
SCAN_END = 14.0
SIGNAL_END = 16.5
IGNITION_END = 17.5
ASCENT_END = 21.5
HOVER_END = 23.0
DESCENT_END = 26.0
LANDING_END = 27.5
RETURN_END = 30.5

IGNITION_TIME = 16.5
HOP_HEIGHT = 4.8

UFO_START = Vec3(13.5, 8.5, 9.0)
ORBIT_RADIUS = 5.6
ORBIT_HEIGHT = 5.7
ORBIT_START_ANGLE = 90.0
ORBIT_END_ANGLE = 300.0
SIGNAL_POINT = Vec3(-6.4, 6.2, 3.0)
DEPARTURE_POINT = Vec3(-8.0, 6.2, 3.2)
FOLLOW_RADIUS = 5.0


def smoothstep(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def smootherstep(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * value * (value * (value * 6.0 - 15.0) + 10.0)


def phase(time: float, start: float, end: float) -> float:
    if end <= start:
        return 0.0
    return max(0.0, min(1.0, (time - start) / (end - start)))


def angle_lerp(start: float, end: float, amount: float) -> float:
    return start + (end - start) * amount


def orbit_position(angle_degrees: float, radius: float, height: float) -> Vec3:
    angle = math.radians(angle_degrees)
    return Vec3(radius * math.sin(angle), height, radius * math.cos(angle))


def heading_to(origin: Vec3, target: Vec3) -> float:
    return math.degrees(math.atan2(target.x - origin.x, target.z - origin.z))


class Mission:
    def __init__(self, rocket: Rocket, ufo: UFO, environment: Environment):
        self.rocket = rocket
        self.ufo = ufo
        self.environment = environment
        self._last_ufo_position = UFO_START.copy()

    # ------------------------------------------------------------------
    def update(self, time: float) -> None:
        time = time % DURATION
        rocket_state = self._rocket_state(time)
        self._apply_rocket(time, rocket_state)
        self._apply_clamps(rocket_state["clamp_open"])
        self._apply_ufo(time, rocket_state)
        self._apply_lights(time)

    # ------------------------------------------------------------------
    def _rocket_state(self, time: float) -> dict:
        altitude = 0.0
        drift_x = 0.0
        drift_z = 0.0
        tilt_z = 0.0
        tilt_x = 0.0
        engine_power = 0.0

        if IGNITION_END <= time < ASCENT_END:
            u = smootherstep(phase(time, IGNITION_END, ASCENT_END))
            altitude = HOP_HEIGHT * u
            drift_x = 0.95 * u
            drift_z = -0.55 * u
            tilt_z = -7.0 * math.sin(math.pi * u)
            tilt_x = 3.0 * math.sin(math.pi * u)
            engine_power = 1.0
        elif ASCENT_END <= time < HOVER_END:
            u = phase(time, ASCENT_END, HOVER_END)
            altitude = HOP_HEIGHT + 0.06 * math.sin(time * 3.0)
            drift_x = 0.95
            drift_z = -0.55
            engine_power = 0.82
        elif HOVER_END <= time < DESCENT_END:
            u = smootherstep(phase(time, HOVER_END, DESCENT_END))
            altitude = HOP_HEIGHT * (1.0 - u)
            drift_x = 0.95 * (1.0 - u)
            drift_z = -0.55 * (1.0 - u)
            tilt_z = 6.0 * math.sin(math.pi * u)
            tilt_x = -2.5 * math.sin(math.pi * u)
            engine_power = 0.62
        elif DESCENT_END <= time < 26.3:
            engine_power = 0.62 * (1.0 - phase(time, DESCENT_END, 26.3))
        elif SIGNAL_END <= time < IGNITION_END:
            # vibração curta enquanto o motor ganha potência
            engine_power = smoothstep(phase(time, SIGNAL_END, IGNITION_END))
        elif SCAN_END <= time < SIGNAL_END:
            engine_power = 0.0

        clamp_open = smoothstep(phase(time, 14.6, 16.2))
        if time >= 26.3:
            clamp_open = 1.0 - smoothstep(phase(time, 26.3, LANDING_END))

        return {
            "altitude": altitude,
            "drift_x": drift_x,
            "drift_z": drift_z,
            "tilt_x": tilt_x,
            "tilt_z": tilt_z,
            "engine_power": engine_power,
            "clamp_open": clamp_open,
        }

    # ------------------------------------------------------------------
    def _apply_rocket(self, time: float, state: dict) -> None:
        root = self.rocket.root
        shake_x = 0.0
        shake_z = 0.0
        if SIGNAL_END <= time < IGNITION_END:
            shake = 0.012 * math.sin(time * 68.0)
            shake_x = shake
            shake_z = 0.008 * math.sin(time * 57.0 + 0.8)

        root.translation = Vec3(
            state["drift_x"] + shake_x,
            ROCKET_BASE_Y + state["altitude"],
            state["drift_z"] + shake_z,
        )
        root.rotation = Vec3(state["tilt_x"], 0.0, state["tilt_z"])

        engine_active = IGNITION_TIME <= time < 26.3
        self.rocket.set_engine(engine_active, time, state["engine_power"])
        self.rocket.update_smoke(time, IGNITION_TIME)

    def _apply_clamps(self, open_amount: float) -> None:
        for arm in self.environment.clamp_arms:
            arm.translation.x = 0.95 + 0.95 * open_amount

    # ------------------------------------------------------------------
    def _apply_ufo(self, time: float, rocket_state: dict) -> None:
        ufo = self.ufo
        rocket_root_y = ROCKET_BASE_Y + rocket_state["altitude"]
        rocket_center = Vec3(0.0, rocket_root_y + 2.4, 0.0)

        beam_active = False
        signal_intensity = 0.08
        bank = 0.0
        tilt = 0.0
        position = UFO_START.copy()
        heading = 0.0

        if time < APPROACH_END:
            u = smoothstep(phase(time, 0.0, APPROACH_END))
            start_orbit = orbit_position(ORBIT_START_ANGLE, ORBIT_RADIUS, ORBIT_HEIGHT)
            position = UFO_START.lerp(start_orbit, u)
            position.y += 0.9 * math.sin(math.pi * u)
            heading = heading_to(position, rocket_center)
            bank = -7.0 * math.sin(math.pi * u)
            signal_intensity = 0.10 + 0.08 * math.sin(time * 4.0)
        elif time < SCAN_END:
            u = smootherstep(phase(time, APPROACH_END, SCAN_END))
            angle = angle_lerp(ORBIT_START_ANGLE, ORBIT_END_ANGLE, u)
            position = orbit_position(angle, ORBIT_RADIUS, ORBIT_HEIGHT)
            position.y += 0.28 * math.sin(time * 1.9)
            heading = heading_to(position, rocket_center)
            bank = -9.0 * math.sin(math.radians(angle - 90.0))
            tilt = 2.0 * math.sin(time * 1.3)
            beam_active = 6.8 <= time <= 13.2
            signal_intensity = 0.18
        elif time < SIGNAL_END:
            u = smoothstep(phase(time, SCAN_END, SIGNAL_END))
            orbit_end = orbit_position(ORBIT_END_ANGLE, ORBIT_RADIUS, ORBIT_HEIGHT)
            position = orbit_end.lerp(SIGNAL_POINT, u)
            position.y += 0.10 * math.sin(time * 2.5)
            heading = heading_to(position, rocket_center)
            bank = -5.0 * (1.0 - u)
            flash = 0.5 + 0.5 * math.sin(time * 18.0)
            signal_intensity = 0.35 + 0.65 * flash
        elif time < IGNITION_END:
            u = smoothstep(phase(time, SIGNAL_END, IGNITION_END))
            position = SIGNAL_POINT.lerp(Vec3(SIGNAL_POINT.x, SIGNAL_POINT.y + 0.15, SIGNAL_POINT.z), u)
            heading = heading_to(position, rocket_center)
            signal_intensity = 1.0
            bank = -3.0
        elif time < ASCENT_END:
            u = phase(time, IGNITION_END, ASCENT_END)
            angle = angle_lerp(ORBIT_END_ANGLE, 355.0, u)
            follow = orbit_position(angle, FOLLOW_RADIUS, 0.0)
            follow = Vec3(
                rocket_state["drift_x"] + follow.x,
                max(6.6, rocket_root_y + 4.9),
                rocket_state["drift_z"] + follow.z,
            )
            blend = smoothstep(phase(time, IGNITION_END, 19.0))
            position = SIGNAL_POINT.lerp(follow, blend)
            position.y = max(6.6, rocket_root_y + 4.9) + 0.10 * math.sin(time * 2.1)
            heading = heading_to(position, rocket_center)
            bank = -10.0 * math.sin(math.pi * u)
            tilt = 3.0 * math.sin(math.pi * u)
            signal_intensity = 0.85
        elif time < HOVER_END:
            u = phase(time, ASCENT_END, HOVER_END)
            angle = angle_lerp(355.0, 380.0, u)
            follow = orbit_position(angle, FOLLOW_RADIUS, 0.0)
            position = Vec3(
                rocket_state["drift_x"] + follow.x,
                rocket_root_y + 4.9 + 0.10 * math.sin(time * 2.0),
                rocket_state["drift_z"] + follow.z,
            )
            heading = heading_to(position, rocket_center)
            bank = -8.0
            signal_intensity = 0.65
        elif time < DESCENT_END:
            u = phase(time, HOVER_END, DESCENT_END)
            angle = angle_lerp(380.0, 425.0, u)
            follow = orbit_position(angle, FOLLOW_RADIUS, 0.0)
            position = Vec3(
                rocket_state["drift_x"] + follow.x,
                max(6.6, rocket_root_y + 4.9),
                rocket_state["drift_z"] + follow.z,
            )
            position.y += 0.10 * math.sin(time * 2.2)
            heading = heading_to(position, rocket_center)
            bank = 6.0 * math.sin(math.pi * u)
            signal_intensity = 0.55
        elif time < LANDING_END:
            u = smoothstep(phase(time, DESCENT_END, LANDING_END))
            angle = 425.0
            follow = orbit_position(angle, FOLLOW_RADIUS, 0.0)
            last_follow = Vec3(
                rocket_state["drift_x"] + follow.x,
                max(6.6, rocket_root_y + 4.9),
                rocket_state["drift_z"] + follow.z,
            )
            position = last_follow.lerp(DEPARTURE_POINT, u)
            heading = heading_to(position, rocket_center)
            signal_intensity = 0.35 * (1.0 - u)
        elif time < RETURN_END:
            u = smoothstep(phase(time, LANDING_END, RETURN_END))
            position = DEPARTURE_POINT.lerp(UFO_START, u)
            position.y += 1.0 * math.sin(math.pi * u)
            direction = UFO_START - DEPARTURE_POINT
            heading = math.degrees(math.atan2(direction.x, direction.z))
            bank = 8.0 * math.sin(math.pi * u)
            signal_intensity = 0.0
        else:
            position = UFO_START.copy()
            heading = 0.0
            signal_intensity = 0.0

        ufo.root.translation = position
        ufo.root.rotation.y = heading
        ufo.update_animation(time, bank, tilt)
        ufo.set_signal(signal_intensity)
        ufo.set_beam(beam_active, rocket_center, time)

        self._last_ufo_position = position

    # ------------------------------------------------------------------
    def _apply_lights(self, time: float) -> None:
        for index, material in enumerate(self.environment.pad_lights):
            if 14.0 <= time < 18.0:
                intensity = 0.75 + 0.25 * (0.5 + 0.5 * math.sin(time * 18.0 + index))
            elif IGNITION_END <= time < ASCENT_END + 1.0:
                intensity = 1.0
            else:
                intensity = 0.45 + 0.20 * (0.5 + 0.5 * math.sin(time * 2.4 + index * 0.7))
            material.emissive = (1.0 * intensity, 0.45 * intensity, 0.08 * intensity)

        beacon = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(time * 3.2))
        if 14.0 <= time < 17.5:
            beacon = 0.7 + 0.3 * (0.5 + 0.5 * math.sin(time * 22.0))
        self.environment.beacon.emissive = (1.0 * beacon, 0.12 * beacon, 0.08 * beacon)

        bunker = 0.65 + 0.35 * (0.5 + 0.5 * math.sin(time * 1.4))
        self.environment.bunker_light.emissive = (
            0.15 * bunker,
            0.75 * bunker,
            1.0 * bunker,
        )

