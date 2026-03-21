"""Entity — just an ID and a bag of components."""

from __future__ import annotations

import uuid
from typing import Type, TypeVar, cast

from nimbus.core.component import Component

T = TypeVar("T", bound=Component)


class Entity:
    """A game object — nothing more than a unique ID and a collection of
    components. All behavior comes from Systems acting on components.

    Usage::

        e = Entity(name="player")
        e.add(Transform(x=100, y=200))
        e.add(PhysicsBody(mass=1.0))

        transform = e.get(Transform)
        transform.x += 10

        e.remove(PhysicsBody)
    """

    def __init__(self, name: str = "") -> None:
        self.id: str = uuid.uuid4().hex[:12]
        self.name: str = name or self.id
        self._components: dict[type, Component] = {}
        self._scene = None  # back-reference set by Scene

    # -- component management ----------------------------------------------

    def add(self, component: Component) -> "Entity":
        """Attach a component. Replaces any existing component of the same type."""
        self._components[type(component)] = component
        return self

    def get(self, component_type: Type[T]) -> T:
        """Get a component by type. Raises KeyError if not present."""
        comp = self._components.get(component_type)
        if comp is None:
            raise KeyError(f"{self.name!r} has no {component_type.__name__} component")
        return cast(T, comp)

    def try_get(self, component_type: Type[T]) -> T | None:
        """Get a component by type, or None if not present."""
        return cast(T, self._components.get(component_type))

    def has(self, *component_types: type) -> bool:
        """True if the entity has ALL of the given component types."""
        return all(ct in self._components for ct in component_types)

    def remove(self, component_type: type) -> None:
        """Remove a component by type (no-op if not present)."""
        self._components.pop(component_type, None)

    def all_components(self) -> list[Component]:
        return list(self._components.values())

    # -- helpers -----------------------------------------------------------

    def destroy(self) -> None:
        """Remove this entity from its scene."""
        if self._scene is not None:
            self._scene.destroy(self)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "components": [c.to_dict() for c in self._components.values()],
        }

    def __repr__(self) -> str:
        comps = ", ".join(type(c).__name__ for c in self._components.values())
        return f"Entity({self.name!r}, [{comps}])"
