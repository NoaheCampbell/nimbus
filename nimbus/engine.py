"""Core engine — runs the pygame game loop and owns the window."""

from __future__ import annotations

import threading
from typing import Any

import pygame

from nimbus.input import Input
from nimbus.core.scene import Scene
from nimbus.systems.physics_system import PhysicsSystem
from nimbus.systems.collision_system import CollisionSystem
from nimbus.systems.script_system import ScriptSystem
from nimbus.systems.render_system import RenderSystem


# Default systems added to every scene (in execution order)
def _default_systems(screen) -> list:
    return [
        ScriptSystem(),
        PhysicsSystem(),
        CollisionSystem(),
        RenderSystem(screen),
    ]


class Engine:
    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        title: str = "Nimbus",
        fps: int = 60,
    ) -> None:
        self.width = width
        self.height = height
        self.title = title
        self.fps = fps

        self._scene: Scene | None = None
        self._running = False
        self._paused = False
        self._lock = threading.Lock()
        self._screen: pygame.Surface | None = None
        self._clock: pygame.time.Clock | None = None

    # -- scene management --------------------------------------------------

    def load_scene(self, scene: Scene) -> None:
        with self._lock:
            self._scene = scene
            if self._screen is not None:
                if scene.width != self.width or scene.height != self.height:
                    self.width = scene.width
                    self.height = scene.height
                    self._screen = pygame.display.set_mode((self.width, self.height))
                scene._load(_default_systems(self._screen))
            # If screen not ready yet, _load will be called in run()

    def get_scene(self) -> Scene | None:
        with self._lock:
            return self._scene

    # -- playback control --------------------------------------------------

    def pause(self) -> None:    self._paused = True
    def resume(self) -> None:   self._paused = False
    def stop(self) -> None:     self._running = False

    @property
    def is_paused(self) -> bool:  return self._paused
    @property
    def is_running(self) -> bool: return self._running

    # -- screenshot --------------------------------------------------------

    def screenshot(self) -> bytes | None:
        if self._screen is None:
            return None
        import io
        from PIL import Image
        raw = pygame.image.tostring(self._screen, "RGB")
        img = Image.frombytes("RGB", (self.width, self.height), raw)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    # -- main loop ---------------------------------------------------------

    def run(self) -> None:
        pygame.init()
        self._screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(self.title)
        self._clock = pygame.time.Clock()
        self._running = True

        # Load any scene that was set before the window existed
        with self._lock:
            if self._scene and not self._scene._loaded:
                self._scene._load(_default_systems(self._screen))

        while self._running:
            dt = self._clock.tick(self.fps) / 1000.0

            Input._frame_reset()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                    break
                Input._handle_event(event)

            if not self._running:
                break

            with self._lock:
                scene = self._scene

            if not self._paused and scene:
                scene.update(dt)
            elif not scene:
                self._screen.fill((20, 20, 20))
                self._draw_idle()

            pygame.display.flip()

        pygame.quit()

    def _draw_idle(self) -> None:
        font = pygame.font.SysFont("monospace", 18)
        surf = font.render("No scene loaded. Use the API to load one.", True, (120, 120, 120))
        self._screen.blit(surf, surf.get_rect(center=(self.width // 2, self.height // 2)))
