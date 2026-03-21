"""RenderSystem — draws all visible entities in layer order."""

from __future__ import annotations

import pygame

from nimbus.core.system import System
from nimbus.components.transform import Transform
from nimbus.components.rect_renderer import RectRenderer
from nimbus.components.sprite_renderer import SpriteRenderer


class RenderSystem(System):
    """Renders entities to the pygame screen.

    Drawing order:
    1. Scene background (bgcolor fill or custom draw_background hook)
    2. All RectRenderer + SpriteRenderer entities, sorted by layer
    """

    def __init__(self, screen: pygame.Surface) -> None:
        self._screen = screen
        self._sprite_cache: dict[str, pygame.Surface] = {}

    def update(self, dt: float, scene) -> None:
        screen = self._screen

        # Background
        if hasattr(scene, "draw_background"):
            scene.draw_background(screen)
        else:
            screen.fill(scene.bgcolor)

        # Collect renderable entities, sort by layer
        renderables = []
        for entity in scene.all_entities():
            t = entity.try_get(Transform)
            if t is None:
                continue
            rr = entity.try_get(RectRenderer)
            sr = entity.try_get(SpriteRenderer)
            if rr and rr.visible:
                renderables.append((rr.layer, entity, t, rr, None))
            if sr and sr.visible:
                renderables.append((sr.layer, entity, t, None, sr))

        renderables.sort(key=lambda r: r[0])

        for _, entity, t, rr, sr in renderables:
            if rr:
                self._draw_rect(t, rr)
            elif sr:
                self._draw_sprite(t, sr)

    def _draw_rect(self, t: Transform, rr: RectRenderer) -> None:
        w = int(rr.width * t.scale_x)
        h = int(rr.height * t.scale_y)
        pygame.draw.rect(
            self._screen,
            rr.color,
            pygame.Rect(int(t.x), int(t.y), w, h),
        )

    def _draw_sprite(self, t: Transform, sr: SpriteRenderer) -> None:
        if not sr.image:
            return
        try:
            if sr.image not in self._sprite_cache:
                self._sprite_cache[sr.image] = pygame.image.load(sr.image).convert_alpha()
            img = self._sprite_cache[sr.image]

            # Scale
            w = int(img.get_width() * t.scale_x)
            h = int(img.get_height() * t.scale_y)
            img = pygame.transform.scale(img, (w, h))

            # Flip
            if sr.flip_x or sr.flip_y:
                img = pygame.transform.flip(img, sr.flip_x, sr.flip_y)

            # Rotation
            if t.rotation:
                img = pygame.transform.rotate(img, -t.rotation)

            # Opacity
            if sr.opacity < 1.0:
                img = img.copy()
                img.set_alpha(int(sr.opacity * 255))

            self._screen.blit(img, (int(t.x), int(t.y)))
        except Exception:
            # Draw a magenta rect as "missing sprite" indicator
            pygame.draw.rect(
                self._screen,
                (255, 0, 255),
                pygame.Rect(int(t.x), int(t.y), 32, 32),
            )
