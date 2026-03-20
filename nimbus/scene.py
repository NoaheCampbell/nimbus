"""Scene — a container for entities that the engine ticks and renders."""

from __future__ import annotations

from typing import Any

from nimbus.entity import Entity


class Scene:
    """Holds a flat list of entities and drives their update / render cycle.

    Scenes can be defined in agent scripts::

        from nimbus import Scene, Entity

        class Ball(Entity):
            ...

        scene = Scene(name="demo", bgcolor=(30, 30, 30))
        scene.add(Ball())
    """

    def __init__(
        self,
        name: str = "default",
        bgcolor: tuple[int, int, int] = (0, 0, 0),
        width: int = 800,
        height: int = 600,
    ) -> None:
        self.name = name
        self.bgcolor = bgcolor
        self.width = width
        self.height = height
        self.entities: list[Entity] = []

    def add(self, entity: Entity) -> Entity:
        """Add an entity and set its back-reference."""
        entity._scene = self
        self.entities.append(entity)
        return entity

    def remove(self, entity: Entity) -> None:
        """Remove an entity from the scene."""
        entity._scene = None
        try:
            self.entities.remove(entity)
        except ValueError:
            pass

    def clear(self) -> None:
        """Remove all entities."""
        for e in self.entities:
            e._scene = None
        self.entities.clear()

    def update(self, dt: float) -> None:
        """Tick every entity."""
        for entity in list(self.entities):
            entity.update(dt)

    def handle_event(self, event: Any) -> None:
        """Forward a pygame event to every entity."""
        for entity in list(self.entities):
            entity.on_event(event)

    def to_dict(self) -> dict:
        """Serialise scene state for the ``/state`` endpoint."""
        return {
            "name": self.name,
            "bgcolor": list(self.bgcolor),
            "width": self.width,
            "height": self.height,
            "entity_count": len(self.entities),
            "entities": [e.to_dict() for e in self.entities],
        }
