"""Renderizador: passe de sombra, passe principal e pós-processamento."""

from __future__ import annotations

import numpy as np
from OpenGL.GL import (
    GL_BACK,
    GL_BLEND,
    GL_CCW,
    GL_COLOR_BUFFER_BIT,
    GL_CULL_FACE,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_FALSE,
    GL_FRAMEBUFFER,
    GL_ONE,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_POLYGON_OFFSET_FILL,
    GL_SRC_ALPHA,
    GL_TRIANGLES,
    GL_TRUE,
    glBindFramebuffer,
    glBindVertexArray,
    glBlendFunc,
    glClear,
    glClearColor,
    glCullFace,
    glDepthMask,
    glDisable,
    glDrawArrays,
    glEnable,
    glFrontFace,
    glGenVertexArrays,
    glPolygonOffset,
    glViewport,
)

from . import matrix
from .light import DirectionalLight
from .object3d import Object3D
from .postprocess import PostProcessor
from .shader import ShaderProgram
from .shadow import ShadowMap

ZENITH_COLOR = (0.020, 0.045, 0.14)
HORIZON_COLOR = (0.95, 0.55, 0.32)
SUN_COLOR = (1.0, 0.72, 0.42)
FOG_START = 30.0
FOG_END = 88.0


class Renderer:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.main_program = ShaderProgram("main.vert", "main.frag")
        self.depth_program = ShaderProgram("depth.vert", "depth.frag")
        self.sky_program = ShaderProgram("sky.vert", "sky.frag")
        self.shadow = ShadowMap(2048)
        self.post = PostProcessor(width, height)
        self.fullscreen_vao = glGenVertexArrays(1)

        self.shadows_enabled = True
        self.bloom_enabled = True
        self.last_shadow_rendered = False

        glEnable(GL_DEPTH_TEST)
        glDepthMask(GL_TRUE)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        glFrontFace(GL_CCW)
        glClearColor(0.02, 0.03, 0.05, 1.0)

    # ------------------------------------------------------------------
    def resize(self, width: int, height: int) -> None:
        self.width = max(1, width)
        self.height = max(1, height)
        self.post.resize(self.width, self.height)

    # ------------------------------------------------------------------
    def render(self, scene, camera) -> None:
        scene.root.update_matrix()

        # 1) passe de profundidade do ponto de vista da luz
        self.last_shadow_rendered = self.shadows_enabled
        if self.shadows_enabled:
            self._render_shadow_pass(scene)

        # 2) destino do passe principal
        if self.bloom_enabled:
            self.post.begin_scene()
        else:
            glBindFramebuffer(GL_FRAMEBUFFER, 0)
            glViewport(0, 0, self.width, self.height)

        glClearColor(0.02, 0.03, 0.05, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self._render_sky(scene, camera)
        self._render_main_pass(scene, camera)

        if self.bloom_enabled:
            self.post.resolve()

    # ------------------------------------------------------------------
    def _render_shadow_pass(self, scene) -> None:
        self.shadow.begin(scene.light)
        glViewport(0, 0, self.shadow.size, self.shadow.size)
        glClear(GL_DEPTH_BUFFER_BIT)

        glEnable(GL_DEPTH_TEST)
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        glEnable(GL_POLYGON_OFFSET_FILL)
        glPolygonOffset(2.0, 4.0)

        self.depth_program.use()
        self.depth_program.set_mat4("u_lightVP", self.shadow.light_vp)
        self._render_depth_tree(scene.root)

        glDisable(GL_POLYGON_OFFSET_FILL)
        self.shadow.end(self.width, self.height)

    def _render_depth_tree(self, node: Object3D) -> None:
        if not node.visible:
            return
        if node.mesh is not None:
            material = node.mesh.material
            if material.cast_shadow and not material.transparent:
                self.depth_program.set_mat4("u_model", node.matrix)
                node.mesh.draw()
        for child in node.children:
            self._render_depth_tree(child)

    # ------------------------------------------------------------------
    def _render_sky(self, scene, camera) -> None:
        glDisable(GL_DEPTH_TEST)
        glDepthMask(GL_FALSE)
        glDisable(GL_CULL_FACE)
        glDisable(GL_BLEND)

        self.sky_program.use()
        inv_view_projection = matrix.inverse(camera.projection @ camera.view)
        self.sky_program.set_mat4("u_invViewProj", inv_view_projection)
        self.sky_program.set_vec3("u_cameraPos", camera.eye)
        self.sky_program.set_vec3("u_sunDir", scene.light.direction_to_light)
        self.sky_program.set_vec3("u_zenithColor", ZENITH_COLOR)
        self.sky_program.set_vec3("u_horizonColor", HORIZON_COLOR)
        self.sky_program.set_vec3("u_sunColor", SUN_COLOR)

        glBindVertexArray(self.fullscreen_vao)
        glDrawArrays(GL_TRIANGLES, 0, 3)
        glBindVertexArray(0)

        glDepthMask(GL_TRUE)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)

    # ------------------------------------------------------------------
    def _render_main_pass(self, scene, camera) -> None:
        glEnable(GL_DEPTH_TEST)
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)

        program = self.main_program
        program.use()
        program.set_mat4("u_view", camera.view)
        program.set_mat4("u_projection", camera.projection)
        program.set_mat4("u_lightVP", self.shadow.light_vp)
        program.set_vec3("u_lightDirection", scene.light.direction_to_light)
        program.set_vec3("u_lightColor", scene.light.color)
        program.set_vec3("u_ambientSky", scene.light.ambient_sky)
        program.set_vec3("u_ambientGround", scene.light.ambient_ground)
        program.set_vec3("u_cameraPos", camera.eye)
        program.set_vec3("u_fogColor", HORIZON_COLOR)
        program.set_float("u_fogStart", FOG_START)
        program.set_float("u_fogEnd", FOG_END)
        program.set_int("u_texture", 0)
        program.set_int("u_shadowMap", 1)
        program.set_float("u_shadowTexel", 1.0 / self.shadow.size)
        program.set_int("u_shadowEnabled", 1 if self.shadows_enabled else 0)

        self.shadow.bind(1)

        self._render_opaque_tree(scene.root)
        self._render_transparent_objects(scene.root, camera)

        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)
        glEnable(GL_CULL_FACE)

    # ------------------------------------------------------------------
    def _draw_mesh(self, node: Object3D, transparent: bool) -> None:
        material = node.mesh.material
        program = self.main_program

        program.set_mat4("u_model", node.matrix)
        program.set_mat3("u_normalMatrix", matrix.normal_matrix(node.matrix))
        program.set_vec3("u_baseColor", material.color)
        program.set_vec3("u_specularColor", material.specular)
        program.set_float("u_shininess", material.shininess)
        program.set_float("u_ambientStrength", material.ambient)
        program.set_vec3("u_emissive", material.emissive)
        program.set_float("u_opacity", material.opacity)
        program.set_int("u_unlit", 1 if material.unlit else 0)
        program.set_int("u_receiveShadow", 1 if material.receive_shadow else 0)
        program.set_int(
            "u_useTexture", 1 if (material.texture is not None and material.use_texture) else 0
        )
        if material.texture is not None and material.use_texture:
            material.texture.bind(0)

        if material.double_sided:
            glDisable(GL_CULL_FACE)
        if transparent:
            glEnable(GL_BLEND)
            glDepthMask(GL_FALSE)
            if material.additive:
                glBlendFunc(GL_SRC_ALPHA, GL_ONE)
            else:
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        node.mesh.draw()
        if material.double_sided:
            glEnable(GL_CULL_FACE)

    def _render_opaque_tree(self, node: Object3D) -> None:
        if not node.visible:
            return
        if node.mesh is not None and not node.mesh.material.transparent:
            self._draw_mesh(node, transparent=False)
        for child in node.children:
            self._render_opaque_tree(child)

    def _render_transparent_objects(self, root: Object3D, camera) -> None:
        objects: list[Object3D] = []

        def collect(node: Object3D) -> None:
            if not node.visible:
                return
            if node.mesh is not None and node.mesh.material.transparent:
                objects.append(node)
            for child in node.children:
                collect(child)

        collect(root)
        if not objects:
            return

        camera_position = camera.eye.array
        objects.sort(
            key=lambda obj: float(np.linalg.norm(obj.world_position() - camera_position)),
            reverse=True,
        )
        for node in objects:
            self._draw_mesh(node, transparent=True)
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)
