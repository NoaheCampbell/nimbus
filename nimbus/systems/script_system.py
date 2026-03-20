"""ScriptSystem — runs Script components, handles hot reload."""

from __future__ import annotations

import traceback

from nimbus.core.system import System
from nimbus.components.script import Script


class ScriptSystem(System):
    """Runs all Script components each frame.

    - Checks for file changes and hot-reloads modified scripts
    - Calls start() on first frame after load/reload
    - Calls update(entity, scene, dt) every frame
    - Captures errors into scene._errors instead of crashing
    """

    def on_scene_load(self, scene) -> None:
        # Force all scripts to load on scene start
        for entity in scene.query(Script):
            script = entity.get(Script)
            script._reload_if_changed()

    def update(self, dt: float, scene) -> None:
        for entity in scene.query(Script):
            script = entity.get(Script)

            # Hot reload
            script._reload_if_changed()

            if script._load_error:
                scene._errors.append({
                    "fn": f"Script({script.path})",
                    "traceback": script._load_error,
                })
                continue

            # start() on first frame (or after reload)
            if not script._started and script._start:
                try:
                    script._start(entity, scene)
                except Exception:
                    scene._errors.append({
                        "fn": f"Script({script.path}).start",
                        "traceback": traceback.format_exc(),
                    })
            script._started = True

            # update()
            if script._update:
                try:
                    script._update(entity, scene, dt)
                except Exception:
                    scene._errors.append({
                        "fn": f"Script({script.path}).update",
                        "traceback": traceback.format_exc(),
                    })
