"""Script component — attaches agent-written logic to an entity."""

from __future__ import annotations

import importlib.util
import traceback
from pathlib import Path
from typing import Callable


class Script:
    """Attaches a Python script to an entity.

    The script file should define any of these functions:

        def start(entity, scene):
            '''Called once when the scene loads.'''

        def update(entity, scene, dt):
            '''Called every frame.'''

        def on_collision(entity, other, scene):
            '''Called when this entity's BoxCollider overlaps another.'''

        def on_destroy(entity, scene):
            '''Called just before this entity is removed.'''

    Hot reload: if the script file changes on disk, the engine will
    automatically reload it on the next frame.
    """

    def __init__(self, path: str) -> None:
        self.path = path
        self._mtime: float = 0
        self._start:        Callable | None = None
        self._update:       Callable | None = None
        self._on_collision: Callable | None = None
        self._on_destroy:   Callable | None = None
        self._load_error:   str | None = None
        self._started = False

    def to_dict(self) -> dict:
        return {
            "type": "Script",
            "path": self.path,
            "load_error": self._load_error,
            "started": self._started,
            "has_update": self._update is not None,
            "has_on_collision": self._on_collision is not None,
        }

    def _reload_if_changed(self) -> None:
        """Reload the script from disk if the file has been modified."""
        try:
            mtime = Path(self.path).stat().st_mtime
        except FileNotFoundError:
            self._load_error = f"Script not found: {self.path}"
            return

        if mtime == self._mtime:
            return  # unchanged

        self._mtime = mtime
        self._load_error = None
        self._started = False  # re-run start() after reload

        try:
            spec = importlib.util.spec_from_file_location("_nimbus_script", self.path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not create module spec for {self.path}")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            self._start        = getattr(mod, "start",        None)
            self._update       = getattr(mod, "update",       None)
            self._on_collision = getattr(mod, "on_collision", None)
            self._on_destroy   = getattr(mod, "on_destroy",   None)
        except Exception:
            self._load_error = traceback.format_exc()
            self._start = self._update = self._on_collision = self._on_destroy = None
