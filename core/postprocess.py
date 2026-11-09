"""Pós-processamento opcional: bloom (brilho) com passes de brilho e blur."""

from __future__ import annotations

from OpenGL.GL import (
    GL_CLAMP_TO_EDGE,
    GL_COLOR_ATTACHMENT0,
    GL_DEPTH_ATTACHMENT,
    GL_DEPTH_COMPONENT24,
    GL_FRAMEBUFFER,
    GL_FRAMEBUFFER_COMPLETE,
    GL_LINEAR,
    GL_RENDERBUFFER,
    GL_RGBA,
    GL_RGBA8,
    GL_TEXTURE0,
    GL_TEXTURE1,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_UNSIGNED_BYTE,
    glActiveTexture,
    glBindFramebuffer,
    glBindRenderbuffer,
    glBindTexture,
    glBindVertexArray,
    glCheckFramebufferStatus,
    glClear,
    glClearColor,
    glDeleteFramebuffers,
    glDeleteRenderbuffers,
    glDeleteTextures,
    glDeleteVertexArrays,
    glDisable,
    glDrawArrays,
    glEnable,
    glFramebufferRenderbuffer,
    glFramebufferTexture2D,
    glGenFramebuffers,
    glGenRenderbuffers,
    glGenTextures,
    glGenVertexArrays,
    glRenderbufferStorage,
    glTexImage2D,
    glTexParameteri,
    glViewport,
    GL_BLEND,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_TRIANGLES,
)

from .shader import ShaderProgram


class PostProcessor:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.bright_program = ShaderProgram("fullscreen.vert", "bloom_bright.frag")
        self.blur_program = ShaderProgram("fullscreen.vert", "bloom_blur.frag")
        self.composite_program = ShaderProgram("fullscreen.vert", "composite.frag")
        self.vao = glGenVertexArrays(1)
        self.scene_fbo = None
        self.scene_texture = None
        self.depth_buffer = None
        self.ping_fbo = None
        self.ping_texture = None
        self.pong_fbo = None
        self.pong_texture = None
        self._create_buffers()

    # ------------------------------------------------------------------
    def _color_texture(self, texture: int, width: int, height: int) -> None:
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGBA8, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None
        )
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

    def _create_buffers(self) -> None:
        self.width = max(1, self.width)
        self.height = max(1, self.height)
        half_w = max(1, self.width // 2)
        half_h = max(1, self.height // 2)

        # Ao redimensionar, libera os buffers antigos antes de recriá-los.
        if self.scene_fbo is not None:
            glDeleteFramebuffers(3, [self.scene_fbo, self.ping_fbo, self.pong_fbo])
            glDeleteTextures(3, [self.scene_texture, self.ping_texture, self.pong_texture])
            glDeleteRenderbuffers(1, [self.depth_buffer])

        self.scene_fbo = glGenFramebuffers(1)
        self.scene_texture = glGenTextures(1)
        self.depth_buffer = glGenRenderbuffers(1)
        self.ping_fbo = glGenFramebuffers(1)
        self.ping_texture = glGenTextures(1)
        self.pong_fbo = glGenFramebuffers(1)
        self.pong_texture = glGenTextures(1)

        # FBO da cena: cor + depth renderbuffer
        self._color_texture(self.scene_texture, self.width, self.height)
        glBindFramebuffer(GL_FRAMEBUFFER, self.scene_fbo)
        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.scene_texture, 0
        )
        glBindRenderbuffer(GL_RENDERBUFFER, self.depth_buffer)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, self.width, self.height)
        glFramebufferRenderbuffer(
            GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, self.depth_buffer
        )
        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError("Framebuffer da cena incompleto")

        # FBOs de brilho em meia resolução
        self._color_texture(self.ping_texture, half_w, half_h)
        glBindFramebuffer(GL_FRAMEBUFFER, self.ping_fbo)
        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.ping_texture, 0
        )
        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError("Framebuffer de bloom (ping) incompleto")

        self._color_texture(self.pong_texture, half_w, half_h)
        glBindFramebuffer(GL_FRAMEBUFFER, self.pong_fbo)
        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.pong_texture, 0
        )
        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError("Framebuffer de bloom (pong) incompleto")

        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glBindTexture(GL_TEXTURE_2D, 0)

    def resize(self, width: int, height: int) -> None:
        self.width = max(1, width)
        self.height = max(1, height)
        self._create_buffers()

    # ------------------------------------------------------------------
    def begin_scene(self) -> None:
        glBindFramebuffer(GL_FRAMEBUFFER, self.scene_fbo)
        glViewport(0, 0, self.width, self.height)

    def _draw_quad(self) -> None:
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, 3)
        glBindVertexArray(0)

    def resolve(self) -> None:
        half_w = max(1, self.width // 2)
        half_h = max(1, self.height // 2)

        glDisable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)
        glClearColor(0.0, 0.0, 0.0, 1.0)

        # 1) extrai as regiões brilhantes
        glBindFramebuffer(GL_FRAMEBUFFER, self.ping_fbo)
        glViewport(0, 0, half_w, half_h)
        glClear(GL_COLOR_BUFFER_BIT)
        self.bright_program.use()
        self.bright_program.set_int("u_scene", 0)
        self.bright_program.set_float("u_threshold", 0.62)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.scene_texture)
        self._draw_quad()

        # 2) blur horizontal
        glBindFramebuffer(GL_FRAMEBUFFER, self.pong_fbo)
        glClear(GL_COLOR_BUFFER_BIT)
        self.blur_program.use()
        self.blur_program.set_int("u_image", 0)
        self.blur_program.set_vec2("u_direction", 1.0 / half_w, 0.0)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.ping_texture)
        self._draw_quad()

        # 3) blur vertical
        glBindFramebuffer(GL_FRAMEBUFFER, self.ping_fbo)
        glClear(GL_COLOR_BUFFER_BIT)
        self.blur_program.use()
        self.blur_program.set_int("u_image", 0)
        self.blur_program.set_vec2("u_direction", 0.0, 1.0 / half_h)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.pong_texture)
        self._draw_quad()

        # 4) composição final na tela
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glViewport(0, 0, self.width, self.height)
        glClear(GL_COLOR_BUFFER_BIT)
        self.composite_program.use()
        self.composite_program.set_int("u_scene", 0)
        self.composite_program.set_int("u_bloom", 1)
        self.composite_program.set_float("u_bloomStrength", 0.85)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.scene_texture)
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.ping_texture)
        self._draw_quad()
        glActiveTexture(GL_TEXTURE0)
        glEnable(GL_DEPTH_TEST)

    def destroy(self) -> None:
        if self.scene_fbo is not None:
            glDeleteFramebuffers(3, [self.scene_fbo, self.ping_fbo, self.pong_fbo])
            glDeleteTextures(3, [self.scene_texture, self.ping_texture, self.pong_texture])
            glDeleteRenderbuffers(1, [self.depth_buffer])
            self.scene_fbo = None
        glDeleteVertexArrays(1, [self.vao])
