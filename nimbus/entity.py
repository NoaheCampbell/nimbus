"""Base Entity class for all game objects."""

from __future__ import annotations

import uuid
from typing import Any


class Entity:
    """A game object with position, size, color, and per-frame behavior.

    Subclass this and override ``update`` / ``on_event`` to add logic.

    Attributes:
        id: Unique identifier (auto-generated).
        x, y: World position (pixels).
        width, height: Bounding-box size (pixels).
        color: RGB tuple used when no sprite is set.
        sprite: Optional path to an image file.
        visible: Whether the entity is drawn.
        tags: Arbitrary set of strings for grouping / querying.
    """

    def __init__(
        self,
        x: float = 0,
        y: float = 0,
        width: int = 32,
        height: int = 32,
        color: tuple[int, int, int] = (255, 255, 255),
        sprite: str | None = None,
        visible: bool = True,
        tags: set[str] | None = None,
    ) -> None:
        self.id: str = uuid.uuid4().hex[:12]
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.sprite = sprite
        self.visible = visible
        self.tags: set[str] = tags or set()
        self._scene: Any = None  # back-reference set by Scene

    # -- lifecycle hooks (override in subclasses) -------------------------

    def update(self, dt: float) -> None:
        """Called every frame. *dt* is seconds since last frame."""

    def on_event(self, event: Any) -> None:
        """Called for each pygame event (key presses, mouse, etc.)."""

    # -- helpers -----------------------------------------------------------

    def overlaps(self, other: Entity) -> bool:
        """Simple AABB collision check."""
        return (
            self.x < other.x + other.width
            and self.x + self.width > other.x
            and self.y < other.y + other.height
            and self.y + self.height > other.y
        )

    def find(self, tag: str) -> list[Entity]:
        """Return all entities in the same scene that have *tag*."""
        if self._scene is None:
            return []
        return [e for e in self._scene.entities if tag in e.tags]

    def destroy(self) -> None:
        """Remove this entity from its scene."""
        if self._scene is not None:
            self._scene.remove(self)

    def to_dict(self) -> dict:
        """Serialise to a JSON-safe dict (used by the state API)."""
        return {
            "id": self.id,
            "type": type(self).__name__,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "color": list(self.color),
            "sprite": self.sprite,
            "visible": self.visible,
            "tags": sorted(self.tags),
        }
