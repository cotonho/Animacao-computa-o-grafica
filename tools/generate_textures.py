"""Gera as texturas de imagem usadas na cena.

As texturas são produzidas proceduralmente (ruído periódico + desenho com
Pillow), portanto não há imagens de terceiros no projeto. Execute:

    python tools/generate_textures.py

Os arquivos resultantes ficam em ``textures/``.
"""

from __future__ import annotations

import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "textures"
OUT.mkdir(exist_ok=True)

RNG = np.random.default_rng(20260215)
RANDOM = random.Random(20260215)


# ----------------------------------------------------------------------
# ruído periódico (tileável)
# ----------------------------------------------------------------------
def periodic_noise(size: int, cells: int, rng: np.random.Generator) -> np.ndarray:
    grid = rng.random((cells, cells)).astype(np.float32)
    coordinate = np.arange(size) * cells / size
    x0 = np.floor(coordinate).astype(int) % cells
    x1 = (x0 + 1) % cells
    t = coordinate - np.floor(coordinate)
    t = t * t * (3.0 - 2.0 * t)

    a = grid[np.ix_(x0, x0)]
    b = grid[np.ix_(x0, x1)]
    c = grid[np.ix_(x1, x0)]
    d = grid[np.ix_(x1, x1)]
    top = a * (1.0 - t)[None, :] + b * t[None, :]
    bottom = c * (1.0 - t)[None, :] + d * t[None, :]
    return top * (1.0 - t)[:, None] + bottom * t[:, None]


def fractal_noise(size: int, octaves=(4, 8, 16, 32, 64)) -> np.ndarray:
    result = np.zeros((size, size), dtype=np.float32)
    total = 0.0
    for index, cells in enumerate(octaves):
        amplitude = 1.0 / (2 ** index)
        result += periodic_noise(size, cells, RNG) * amplitude
        total += amplitude
    return result / total


def to_image(array: np.ndarray) -> Image.Image:
    array = np.clip(array, 0.0, 1.0)
    return Image.fromarray(np.uint8(array * 255.0 + 0.5), mode="RGB")


def add_grain(image: Image.Image, amount: float = 0.035) -> Image.Image:
    array = np.asarray(image).astype(np.float32) / 255.0
    noise = RNG.normal(0.0, amount, array.shape[:2])[..., None]
    return to_image(array + noise)


def load_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf") if bold else Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf") if bold else Path("C:/Windows/Fonts/segoeui.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


# ----------------------------------------------------------------------
# areia do deserto
# ----------------------------------------------------------------------
def make_sand() -> None:
    size = 512
    fine = fractal_noise(size, (4, 8, 16, 32, 64))
    coarse = fractal_noise(size, (2, 4, 8, 16))
    xx = np.arange(size)[None, :]
    yy = np.arange(size)[:, None]

    ripple = 0.5 + 0.5 * np.sin((xx * 9 + yy * 3) * math.tau / size + coarse * 9.0)
    value = 0.46 + 0.20 * fine + 0.10 * coarse + 0.035 * ripple

    base = np.zeros((size, size, 3), dtype=np.float32)
    base[..., 0] = value * 1.00 + 0.16
    base[..., 1] = value * 0.82 + 0.10
    base[..., 2] = value * 0.58 + 0.05

    # pequenos seixos escuros
    pebbles = fractal_noise(size, (128, 256))
    mask = pebbles > 0.72
    base[mask] *= 0.72

    image = add_grain(to_image(base), 0.02)
    image.save(OUT / "sand.png")
    print("sand.png")


# ----------------------------------------------------------------------
# metal com painéis (torre, disco, base)
# ----------------------------------------------------------------------
def make_metal_panels() -> None:
    size = 512
    noise = fractal_noise(size, (4, 8, 16, 32, 64))
    base = np.zeros((size, size, 3), dtype=np.float32)
    value = 0.34 + 0.14 * noise
    base[..., 0] = value * 0.92
    base[..., 1] = value * 1.00
    base[..., 2] = value * 1.12

    image = to_image(base)
    draw = ImageDraw.Draw(image)

    panel = 128
    for offset in range(0, size + 1, panel):
        draw.line([(offset, 0), (offset, size)], fill=(48, 56, 66), width=3)
        draw.line([(0, offset), (size, offset)], fill=(48, 56, 66), width=3)
        draw.line([(offset + 2, 0), (offset + 2, size)], fill=(96, 108, 122), width=1)
        draw.line([(0, offset + 2), (size, offset + 2)], fill=(96, 108, 122), width=1)

    # rebites
    for gx in range(0, size, panel):
        for gy in range(0, size, panel):
            for dx, dy in ((14, 14), (panel - 14, 14), (14, panel - 14), (panel - 14, panel - 14)):
                x, y = gx + dx, gy + dy
                if 0 <= x < size and 0 <= y < size:
                    draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(150, 160, 172))
                    draw.ellipse((x - 1, y - 1, x + 1, y + 1), fill=(70, 78, 88))

    # riscos
    for _ in range(90):
        x0 = RANDOM.randrange(size)
        y0 = RANDOM.randrange(size)
        length = RANDOM.randrange(8, 50)
        angle = RANDOM.uniform(-0.5, 0.5)
        x1 = int(x0 + math.cos(angle) * length)
        y1 = int(y0 + math.sin(angle) * length)
        shade = RANDOM.randrange(100, 150)
        draw.line([(x0, y0), (x1, y1)], fill=(shade, shade + 6, shade + 12), width=1)

    image = add_grain(image, 0.015)
    image.save(OUT / "metal_panels.png")
    print("metal_panels.png")


# ----------------------------------------------------------------------
# fuselagem do foguete
# ----------------------------------------------------------------------
def make_rocket_body() -> None:
    width, height = 512, 512
    base = np.zeros((height, width, 3), dtype=np.float32)
    base[..., 0] = 0.90
    base[..., 1] = 0.88
    base[..., 2] = 0.83

    image = to_image(base)
    draw = ImageDraw.Draw(image)

    # faixas horizontais
    draw.rectangle((0, 0, width, 58), fill=(196, 32, 38))
    draw.rectangle((0, 58, width, 70), fill=(238, 226, 205))
    draw.rectangle((0, 70, width, 96), fill=(34, 66, 138))
    draw.rectangle((0, 96, width, 108), fill=(238, 226, 205))
    draw.rectangle((0, 432, width, 456), fill=(34, 66, 138))
    draw.rectangle((0, 456, width, 512), fill=(196, 32, 38))

    # emendas verticais e rebites
    for x in range(32, width, 64):
        draw.line([(x, 0), (x, height)], fill=(206, 198, 184), width=2)
    for x in range(16, width, 32):
        for y in range(118, 430, 28):
            draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(180, 174, 164))

    # desgaste leve
    image = add_grain(image, 0.012)
    image.save(OUT / "rocket_body.png")
    print("rocket_body.png")


# ----------------------------------------------------------------------
# plataforma de lançamento
# ----------------------------------------------------------------------
def make_pad() -> None:
    size = 512
    noise = fractal_noise(size, (4, 8, 16, 32, 64))
    base = np.zeros((size, size, 3), dtype=np.float32)
    value = 0.44 + 0.13 * noise
    base[..., 0] = value
    base[..., 1] = value * 1.01
    base[..., 2] = value * 1.02

    image = to_image(base)
    draw = ImageDraw.Draw(image)

    # borda de perigo
    border = 46
    stripe = 24
    for y in range(0, size, stripe):
        for x in range(0, size, stripe):
            if (x // stripe + y // stripe) % 2 == 0:
                color = (226, 178, 30)
            else:
                color = (36, 36, 38)
            if x < border or x >= size - border or y < border or y >= size - border:
                draw.rectangle((x, y, x + stripe, y + stripe), fill=color)

    # círculo central e marcas de queimadura
    draw.ellipse((92, 92, size - 92, size - 92), outline=(196, 190, 180), width=4)
    draw.ellipse((116, 116, size - 116, size - 116), outline=(150, 146, 140), width=2)

    scorch = np.zeros((size, size), dtype=np.float32)
    yy, xx = np.mgrid[0:size, 0:size]
    distance = np.sqrt((xx - size / 2) ** 2 + (yy - size / 2) ** 2) / (size / 2)
    scorch = np.clip(1.0 - distance * 1.7, 0.0, 1.0) ** 2
    scorch *= 0.55 + 0.45 * fractal_noise(size, (8, 16, 32))
    array = np.asarray(image).astype(np.float32) / 255.0
    array = array * (1.0 - 0.42 * scorch[..., None])
    image = to_image(array)
    draw = ImageDraw.Draw(image)

    # rachaduras
    for _ in range(16):
        x = RANDOM.randrange(70, size - 70)
        y = RANDOM.randrange(70, size - 70)
        points = [(x, y)]
        for _ in range(RANDOM.randrange(3, 7)):
            x += RANDOM.randrange(-22, 23)
            y += RANDOM.randrange(-22, 23)
            points.append((x, y))
        draw.line(points, fill=(70, 68, 66), width=2)

    # identificação
    font = load_font(58, bold=True)
    text = "LC-7"
    bbox = draw.textbbox((0, 0), text, font=font)
    draw.text(
        (size / 2 - (bbox[2] - bbox[0]) / 2, 348),
        text,
        font=font,
        fill=(226, 178, 30),
    )
    font_small = load_font(24, bold=True)
    text = "AURORA TEST RANGE"
    bbox = draw.textbbox((0, 0), text, font=font_small)
    draw.text(
        (size / 2 - (bbox[2] - bbox[0]) / 2, 414),
        text,
        font=font_small,
        fill=(210, 205, 196),
    )

    image = add_grain(image, 0.014)
    image.save(OUT / "pad.png")
    print("pad.png")


# ----------------------------------------------------------------------
# casco do disco voador
# ----------------------------------------------------------------------
def make_ufo_hull() -> None:
    size = 512
    noise = fractal_noise(size, (4, 8, 16, 32, 64))
    base = np.zeros((size, size, 3), dtype=np.float32)
    value = 0.52 + 0.12 * noise
    base[..., 0] = value * 0.88
    base[..., 1] = value * 0.96
    base[..., 2] = value * 1.08

    image = to_image(base)
    draw = ImageDraw.Draw(image)

    # painéis horizontais (latitudes da esfera)
    for y in range(0, size, 64):
        draw.line([(0, y), (size, y)], fill=(54, 62, 74), width=3)
        draw.line([(0, y + 3), (size, y + 3)], fill=(120, 132, 148), width=1)
    # emendas verticais
    for x in range(0, size, 86):
        draw.line([(x, 0), (x, size)], fill=(58, 66, 78), width=2)

    # rebites
    for x in range(0, size, 43):
        for y in range(20, size, 64):
            draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(160, 172, 186))

    # detalhe avermelhado (faixa de identificação)
    draw.rectangle((0, 236, size, 246), fill=(150, 54, 48))

    for _ in range(45):
        x0 = RANDOM.randrange(size)
        y0 = RANDOM.randrange(size)
        draw.line(
            [(x0, y0), (x0 + RANDOM.randrange(-30, 31), y0 + RANDOM.randrange(-30, 31))],
            fill=(120, 130, 142),
            width=1,
        )

    image = add_grain(image, 0.012)
    image.save(OUT / "ufo_hull.png")
    print("ufo_hull.png")


if __name__ == "__main__":
    make_sand()
    make_metal_panels()
    make_rocket_body()
    make_pad()
    make_ufo_hull()
    print(f"Texturas geradas em {OUT}")
