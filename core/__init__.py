"""Framework gráfico reduzido, inspirado em Stemkoski & Pascale (2022).

Módulos:
    matrix      transformações 4x4
    vector      vetor 3D
    geometry    primitivas trianguladas
    mesh        VAO/VBO de uma geometria
    material    parâmetros de superfície
    texture     textura de imagem
    object3d    hierarquia de cena
    light       luz direcional e câmera orbital
    shadow      shadow mapping
    shader      programa GLSL e uniforms
    renderer    passes de renderização
    postprocess bloom
    scene       agregação raiz/câmera/luz
"""

from .light import DirectionalLight, OrbitCamera
from .material import Material
from .object3d import Object3D
from .scene import Scene
from .texture import Texture
from .vector import Vec3

__all__ = [
    "DirectionalLight",
    "OrbitCamera",
    "Material",
    "Object3D",
    "Scene",
    "Texture",
    "Vec3",
]
