"""Materiais: parâmetros de superfície enviados aos shaders."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

Color = Tuple[float, float, float]


@dataclass
class Material:
    # Cor base (multiplica a textura, quando existir)
    color: Color = (0.8, 0.8, 0.8)
    # Coeficientes do modelo de Blinn-Phong
    specular: Color = (0.3, 0.3, 0.3)
    shininess: float = 32.0
    ambient: float = 1.0
    # Emissão somada à cor final (luzes, janelas, chamas)
    emissive: Color = (0.0, 0.0, 0.0)
    # Textura de imagem (Texture) e flag para usar/ignorar
    texture: Optional[object] = None
    use_texture: bool = True
    # Transparência / blending
    opacity: float = 1.0
    transparent: bool = False
    additive: bool = False
    double_sided: bool = False
    # Participação nas sombras
    cast_shadow: bool = True
    receive_shadow: bool = True
    # Material sem iluminação (efeitos e luzes)
    unlit: bool = False

    def clone(self) -> "Material":
        return Material(
            color=self.color,
            specular=self.specular,
            shininess=self.shininess,
            ambient=self.ambient,
            emissive=self.emissive,
            texture=self.texture,
            use_texture=self.use_texture,
            opacity=self.opacity,
            transparent=self.transparent,
            additive=self.additive,
            double_sided=self.double_sided,
            cast_shadow=self.cast_shadow,
            receive_shadow=self.receive_shadow,
            unlit=self.unlit,
        )
