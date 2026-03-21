"""Scene — owns entities and drives systems."""

from __future__ import annotations

import traceback
from typing import Type, TypeVar

from nimbus.core.entity import Entity
from nimbus.core.component import Component
from nimbus.core.system import System

T = TypeVar("T", bound=Component)


class Scene:
    """The active game world. Holds a flat list of entities and an ordered
    list of systems. Each frame: update all systems in order.

    Usage in agent scripts::

        from nimbus.core.scene import Scene
        from nimbus.components.transform import Transform
        from nimbus.components.rect_renderer import RectRenderer

        class MyScene(Scene):
            def on_load(self):
                player = Entity(name="player")
                player.add(Transform(x=100, y=100))
                player.add(RectRenderer(width=32, height=32, color=(0, 120, 255)))
                self.add(player)

        scene = MyScene(name="level1")
    """

    def __init__(
        self,
        name: str = "default",
        width: int = 800,
        height: int = 600,
        bgcolor: tuple = (0, 0, 0),
    ) -> None:
        self.name = name
        self.width = width
        self.height = height
        self.bgcolor = bgcolor

        self._entities: dict[str, Entity] = {}
        self._systems: list[System] = []
        self._errors: list[dict] = []   # captured runtime errors
        self._loaded = False

        # Pending adds/removes (applied at start of next frame to avoid
        # modifying the list while iterating)
        self._pending_add: list[Entity] = []
        self._pending_remove: list[str] = []

    # -- lifecycle ---------------------------------------------------------

    def _load(self, default_systems: list[System]) -> None:
        """Called by the engine when this scene becomes active."""
        for sys in default_systems:
            if not any(type(s) == type(sys) for s in self._systems):
                self._systems.append(sys)
        for system in self._systems:
            self._safe_call(system.on_scene_load, self)
        self.on_load()
        self._loaded = True

    def on_load(self) -> None:
        """Override in subclasses to set up the scene."""

    # -- entity management -------------------------------------------------

    def add(self, entity: Entity) -> Entity:
        """Add an entity to the scene (deferred to next frame)."""
        entity._scene = self
        self._pending_add.append(entity)
        return entity

    def destroy(self, entity: Entity) -> None:
        """Remove an entity from the scene (deferred to next frame)."""
        self._pending_remove.append(entity.id)

    def get(self, entity_id: str) -> Entity | None:
        return self._entities.get(entity_id)

    def find(self, name: str) -> Entity | None:
        for e in self._entities.values():
            if e.name == name:
                return e
        return None

    def query(self, *component_types: type) -> list[Entity]:
        """Return all entities that have ALL of the given component types."""
        return [e for e in self._entities.values() if e.has(*component_types)]

    def all_entities(self) -> list[Entity]:
        return list(self._entities.values())

    # -- systems -----------------------------------------------------------

    def add_system(self, system: System) -> None:
        self._systems.append(system)

    def get_system(self, system_type: type) -> System | None:
        for s in self._systems:
            if type(s) == system_type:
                return s
        return None

    # -- update loop -------------------------------------------------------

    def update(self, dt: float) -> None:
        """Called every frame by the engine."""
        # Apply pending entity changes
        self._flush_pending()

        # Run all enabled systems
        for system in self._systems:
            if system.enabled:
                self._safe_call(system.update, dt, self)

    def _flush_pending(self) -> None:
        for entity in self._pending_add:
            self._entities[entity.id] = entity
            for system in self._systems:
                self._safe_call(system.on_entity_added, entity, self)
        self._pending_add.clear()

        for eid in self._pending_remove:
            entity = self._entities.pop(eid, None)
            if entity:
                entity._scene = None
                for system in self._systems:
                    self._safe_call(system.on_entity_removed, entity, self)
        self._pending_remove.clear()

    # -- error capture -----------------------------------------------------

    def _safe_call(self, fn, *args) -> None:
        """Call fn(*args), capturing any exception into self._errors."""
        try:
            fn(*args)
        except Exception:
            error = {
                "fn": getattr(fn, "__qualname__", str(fn)),
                "traceback": traceback.format_exc(),
            }
            self._errors.append(error)
            # Keep last 50 errors max
            if len(self._errors) > 50:
                self._errors = self._errors[-50:]

    def pop_errors(self) -> list[dict]:
        """Return and clear all captured errors."""
        errors = list(self._errors)
        self._errors.clear()
        return errors

    # -- serialisation -----------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "bgcolor": list(self.bgcolor),
            "entity_count": len(self._entities),
            "entities": [e.to_dict() for e in self._entities.values()],
            "systems": [type(s).__name__ for s in self._systems if s.enabled],
            "pending_errors": len(self._errors),
        }
