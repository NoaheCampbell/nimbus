"""Core engine — runs the pygame game loop and owns the window."""

from __future__ import annotations

import threading
import time
from typing import Any

import pygame

from nimbus.input import Input
from nimbus.scene import Scene


class Engine:
    """Manages the pygame window, game loop, and active scene.

    The engine runs on the main thread (required by pygame on macOS/Windows).
    The FastAPI server runs on a daemon thread alongside it.

    Usage::

        engine = Engine(width=800, height=600, title="My Game", fps=60)
        engine.load_scene(my_scene)
        engine.run()   # blocks until window is closed
    """

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

        # Initialised in run()
        self._screen: pygame.Surface | None = None
        self._clock: pygame.time.Clock | None = None

    # -- scene management --------------------------------------------------

    def load_scene(self, scene: Scene) -> None:
        """Replace the active scene (thread-safe)."""
        with self._lock:
            self._scene = scene
            # Resize window to match scene dimensions if engine already running
            if self._screen is not None and (
                scene.width != self.width or scene.height != self.height
            ):
                self.width = scene.width
                self.height = scene.height
                self._screen = pygame.display.set_mode((self.width, self.height))

    def get_scene(self) -> Scene | None:
        with self._lock:
            return self._scene

    # -- playback control --------------------------------------------------

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def stop(self) -> None:
        self._running = False

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def is_running(self) -> bool:
        return self._running

    # -- screenshot --------------------------------------------------------

    def screenshot(self) -> bytes | None:
        """Capture the current frame as PNG bytes. Returns None if no window."""
        if self._screen is None:
            return None
        import io
        from PIL import Image

        # pygame surface → PIL Image → PNG bytes
        raw = pygame.image.tostring(self._screen, "RGB")
        img = Image.frombytes("RGB", (self.width, self.height), raw)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    # -- main loop ---------------------------------------------------------

    def run(self) -> None:
        """Start the engine. Blocks until the window is closed."""
        pygame.init()
        self._screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(self.title)
        self._clock = pygame.time.Clock()
        self._running = True

        while self._running:
            dt = self._clock.tick(self.fps) / 1000.0  # seconds

            # -- event handling --
            Input._frame_reset()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                    break
                Input._handle_event(event)
                with self._lock:
                    if self._scene:
                        self._scene.handle_event(event)

            if not self._running:
                break

            # -- update --
            if not self._paused:
                with self._lock:
                    if self._scene:
                        self._scene.update(dt)

            # -- render --
            with self._lock:
                scene = self._scene

            if scene:
                self._screen.fill(scene.bgcolor)
                self._render_scene(scene)
            else:
                self._screen.fill((20, 20, 20))
                self._draw_idle_screen()

            pygame.display.flip()

        pygame.quit()

    # -- rendering helpers -------------------------------------------------

    def _render_scene(self, scene: Scene) -> None:
        for entity in scene.entities:
            if not entity.visible:
                continue
            if entity.sprite:
                self._draw_sprite(entity)
            else:
                self._draw_rect(entity)

    def _draw_rect(self, entity: Any) -> None:
        pygame.draw.rect(
            self._screen,
            entity.color,
            pygame.Rect(int(entity.x), int(entity.y), entity.width, entity.height),
        )

    def _draw_sprite(self, entity: Any) -> None:
        try:
            img = pygame.image.load(entity.sprite).convert_alpha()
            img = pygame.transform.scale(img, (entity.width, entity.height))
            self._screen.blit(img, (int(entity.x), int(entity.y)))
        except Exception:
            # Fall back to colored rect if sprite can't be loaded
            self._draw_rect(entity)

    def _draw_idle_screen(self) -> None:
        font = pygame.font.SysFont("monospace", 18)
        surf = font.render("No scene loaded. Use the API to load one.", True, (120, 120, 120))
        rect = surf.get_rect(center=(self.width // 2, self.height // 2))
        self._screen.blit(surf, rect)
