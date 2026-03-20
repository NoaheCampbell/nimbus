"""Base System class — all logic lives here, not in components."""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nimbus.core.scene import Scene


class System:
    """Base class for all systems.

    Systems process entities every frame. Each system should focus on one
    domain (physics, rendering, scripts, collisions, etc.).

    Override ``update`` for per-frame logic and ``on_scene_load`` for
    one-time initialisation when a scene becomes active.
    """

    # Set to False to temporarily disable a system via API
    enabled: bool = True

    def on_scene_load(self, scene: "Scene") -> None:
        """Called once when the scene is first loaded."""

    def update(self, dt: float, scene: "Scene") -> None:
        """Called every frame. dt is seconds since last frame."""

    def on_entity_added(self, entity, scene: "Scene") -> None:
        """Called when an entity is added to the scene."""

    def on_entity_removed(self, entity, scene: "Scene") -> None:
        """Called when an entity is removed from the scene."""
