"""Base Component class — pure data, no logic."""

from __future__ import annotations
from typing import Any


class Component:
    """Base class for all components. Subclasses should declare their fields
    as regular attributes set in __init__.

    Components are pure data containers — all logic lives in Systems.
    """

    def to_dict(self) -> dict:
        """Serialise to a JSON-safe dict for the state API.
        Override to customise; default reflects all public attributes."""
        result = {"type": type(self).__name__}
        for key, val in self.__dict__.items():
            if key.startswith("_"):
                continue
            # Make common types JSON-safe
            if isinstance(val, (int, float, str, bool, type(None))):
                result[key] = val
            elif isinstance(val, (list, tuple)):
                result[key] = list(val)
            elif isinstance(val, set):
                result[key] = sorted(val)
            elif isinstance(val, dict):
                result[key] = val
            else:
                result[key] = str(val)
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "Component":
        """Reconstruct from a dict (used by the API to update components)."""
        obj = cls.__new__(cls)
        obj.__init__()
        for key, val in data.items():
            if key != "type" and hasattr(obj, key):
                setattr(obj, key, val)
        return obj
