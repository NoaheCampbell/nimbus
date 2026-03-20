"""Behavioral assertion system — agents verify game state without vision."""

from __future__ import annotations

from typing import Any


class AssertionError(Exception):
    pass


class EntityAssertion:
    """Fluent assertion builder for a single entity."""

    def __init__(self, entity, results: list):
        self._entity = entity
        self._results = results

    def has_component(self, component_type: type) -> "EntityAssertion":
        name = component_type.__name__
        passed = self._entity.has(component_type)
        self._results.append({
            "assertion": f"{self._entity.name}.has_component({name})",
            "passed": passed,
            "detail": None if passed else f"Entity has no {name} component",
        })
        return self

    def component(self, component_type: type) -> "ComponentAssertion":
        comp = self._entity.try_get(component_type)
        return ComponentAssertion(self._entity, component_type, comp, self._results)

    def exists(self) -> "EntityAssertion":
        self._results.append({
            "assertion": f"{self._entity.name}.exists",
            "passed": True,
            "detail": None,
        })
        return self


class ComponentAssertion:
    """Fluent assertion builder for a component's values."""

    def __init__(self, entity, component_type, component, results: list):
        self._entity = entity
        self._ctype = component_type.__name__
        self._comp = component
        self._results = results

    def _record(self, assertion: str, passed: bool, detail: str | None = None):
        self._results.append({
            "assertion": f"{self._entity.name}.{self._ctype}.{assertion}",
            "passed": passed,
            "detail": detail,
        })
        return self

    def equals(self, field: str, value: Any) -> "ComponentAssertion":
        if self._comp is None:
            return self._record(f"{field} == {value!r}", False, f"Component {self._ctype} not found")
        actual = getattr(self._comp, field, None)
        passed = actual == value
        return self._record(f"{field} == {value!r}", passed,
                            None if passed else f"got {actual!r}")

    def near(self, field: str, value: float, tolerance: float = 5.0) -> "ComponentAssertion":
        if self._comp is None:
            return self._record(f"{field} ≈ {value}", False, f"Component {self._ctype} not found")
        actual = getattr(self._comp, field, None)
        passed = actual is not None and abs(actual - value) <= tolerance
        return self._record(f"{field} ≈ {value} (±{tolerance})", passed,
                            None if passed else f"got {actual!r} (diff={abs(actual - value):.2f})")

    def greater_than(self, field: str, value: float) -> "ComponentAssertion":
        if self._comp is None:
            return self._record(f"{field} > {value}", False, f"Component {self._ctype} not found")
        actual = getattr(self._comp, field, None)
        passed = actual is not None and actual > value
        return self._record(f"{field} > {value}", passed,
                            None if passed else f"got {actual!r}")

    def less_than(self, field: str, value: float) -> "ComponentAssertion":
        if self._comp is None:
            return self._record(f"{field} < {value}", False, f"Component {self._ctype} not found")
        actual = getattr(self._comp, field, None)
        passed = actual is not None and actual < value
        return self._record(f"{field} < {value}", passed,
                            None if passed else f"got {actual!r}")

    def between(self, field: str, lo: float, hi: float) -> "ComponentAssertion":
        if self._comp is None:
            return self._record(f"{lo} <= {field} <= {hi}", False, f"Component {self._ctype} not found")
        actual = getattr(self._comp, field, None)
        passed = actual is not None and lo <= actual <= hi
        return self._record(f"{lo} <= {field} <= {hi}", passed,
                            None if passed else f"got {actual!r}")


class SceneAssertions:
    """Run assertions against a scene and return structured pass/fail results.

    Usage (via POST /assert)::

        {
          "assertions": [
            {"entity": "player", "component": "Transform", "field": "x", "op": "near", "value": 100, "tolerance": 5},
            {"entity": "player", "component": "PhysicsBody", "field": "velocity_y", "op": "less_than", "value": 0},
            {"entity": "enemy", "op": "exists"}
          ]
        }
    """

    def __init__(self, scene) -> None:
        self._scene = scene

    def run(self, assertions: list[dict]) -> dict:
        """Run a list of assertion dicts, return results."""
        results = []

        for a in assertions:
            entity_name = a.get("entity")
            entity = self._scene.find(entity_name) if entity_name else None

            if entity is None:
                results.append({
                    "assertion": f"{entity_name}.exists",
                    "passed": False,
                    "detail": f"Entity '{entity_name}' not found in scene",
                })
                continue

            op = a.get("op", "exists")

            if op == "exists":
                results.append({
                    "assertion": f"{entity_name}.exists",
                    "passed": True,
                    "detail": None,
                })
                continue

            # Component assertions
            component_name = a.get("component")
            field = a.get("field")
            value = a.get("value")
            tolerance = a.get("tolerance", 5.0)

            # Resolve component type by name
            comp = self._resolve_component(entity, component_name)
            actual = getattr(comp, field, None) if comp else None

            if op == "equals":
                passed = actual == value
                results.append({
                    "assertion": f"{entity_name}.{component_name}.{field} == {value!r}",
                    "passed": passed,
                    "detail": None if passed else f"got {actual!r}",
                })
            elif op == "near":
                passed = actual is not None and abs(actual - value) <= tolerance
                results.append({
                    "assertion": f"{entity_name}.{component_name}.{field} ≈ {value} (±{tolerance})",
                    "passed": passed,
                    "detail": None if passed else f"got {actual!r}",
                })
            elif op == "greater_than":
                passed = actual is not None and actual > value
                results.append({
                    "assertion": f"{entity_name}.{component_name}.{field} > {value}",
                    "passed": passed,
                    "detail": None if passed else f"got {actual!r}",
                })
            elif op == "less_than":
                passed = actual is not None and actual < value
                results.append({
                    "assertion": f"{entity_name}.{component_name}.{field} < {value}",
                    "passed": passed,
                    "detail": None if passed else f"got {actual!r}",
                })
            elif op == "between":
                lo, hi = a.get("lo", 0), a.get("hi", 0)
                passed = actual is not None and lo <= actual <= hi
                results.append({
                    "assertion": f"{entity_name}.{component_name}.{field} between {lo} and {hi}",
                    "passed": passed,
                    "detail": None if passed else f"got {actual!r}",
                })
            else:
                results.append({
                    "assertion": f"unknown op: {op}",
                    "passed": False,
                    "detail": f"Unknown assertion op '{op}'",
                })

        total = len(results)
        passed = sum(1 for r in results if r["passed"])
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "results": results,
        }

    def _resolve_component(self, entity, name: str):
        """Find a component by its class name."""
        for comp in entity.all_components():
            if type(comp).__name__ == name:
                return comp
        return None
