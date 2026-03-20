"""Thin input-state wrapper around pygame so agent scripts don't need to
import pygame directly."""

from __future__ import annotations

import pygame

# Maps friendly names → pygame key constants.
_KEY_MAP: dict[str, int] = {
    "up": pygame.K_UP,
    "down": pygame.K_DOWN,
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "space": pygame.K_SPACE,
    "return": pygame.K_RETURN,
    "escape": pygame.K_ESCAPE,
    "lshift": pygame.K_LSHIFT,
    "rshift": pygame.K_RSHIFT,
    "tab": pygame.K_TAB,
}
# Add a-z and 0-9 automatically.
for _c in "abcdefghijklmnopqrstuvwxyz":
    _KEY_MAP[_c] = getattr(pygame, f"K_{_c}")
for _d in "0123456789":
    _KEY_MAP[_d] = getattr(pygame, f"K_{_d}")


def _resolve(name: str) -> int:
    name = name.lower()
    if name in _KEY_MAP:
        return _KEY_MAP[name]
    # Fall back to pygame constant lookup (e.g. "K_F1").
    attr = name if name.startswith("K_") else f"K_{name}"
    val = getattr(pygame, attr, None)
    if val is not None:
        return val
    raise ValueError(f"Unknown key name: {name!r}")


class Input:
    """Static helper that agent scripts use for polling input state.

    Usage::

        from nimbus import Input

        if Input.key_held("right"):
            self.x += speed * dt
        if Input.key_pressed("space"):
            self.jump()
    """

    # Updated each frame by the engine.
    _keys_pressed: set[int] = set()
    _keys_released: set[int] = set()

    @staticmethod
    def key_held(name: str) -> bool:
        """True while the key is held down (polled every frame)."""
        return pygame.key.get_pressed()[_resolve(name)]

    @staticmethod
    def key_pressed(name: str) -> bool:
        """True only on the frame the key was first pressed."""
        return _resolve(name) in Input._keys_pressed

    @staticmethod
    def key_released(name: str) -> bool:
        """True only on the frame the key was released."""
        return _resolve(name) in Input._keys_released

    @staticmethod
    def mouse_pos() -> tuple[int, int]:
        """Current mouse position in window coordinates."""
        return pygame.mouse.get_pos()

    @staticmethod
    def mouse_button(button: int = 1) -> bool:
        """True while a mouse button is held (1=left, 2=middle, 3=right)."""
        return pygame.mouse.get_pressed()[button - 1]

    # -- internal (called by the engine) -----------------------------------

    @classmethod
    def _frame_reset(cls) -> None:
        cls._keys_pressed.clear()
        cls._keys_released.clear()

    @classmethod
    def _handle_event(cls, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            cls._keys_pressed.add(event.key)
        elif event.type == pygame.KEYUP:
            cls._keys_released.add(event.key)
