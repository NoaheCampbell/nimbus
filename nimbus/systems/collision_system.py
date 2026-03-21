"""CollisionSystem — AABB detection, fires on_collision callbacks."""

from __future__ import annotations

import traceback

from nimbus.core.system import System
from nimbus.components.transform import Transform
from nimbus.components.box_collider import BoxCollider
from nimbus.components.script import Script


def _aabb(ax, ay, aw, ah, bx, by, bw, bh) -> bool:
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


class CollisionSystem(System):
    """Brute-force AABB collision detection (fine for small entity counts).

    When two colliders overlap:
    - Fires on_collision(entity, other, scene) on both entities' Script components
    - If neither is a trigger, applies a simple separation push
    """

    def update(self, dt: float, scene) -> None:
        collidables = scene.query(Transform, BoxCollider)

        for i, a in enumerate(collidables):
            at = a.get(Transform)
            ac = a.get(BoxCollider)
            ax = at.x + ac.offset_x
            ay = at.y + ac.offset_y

            for b in collidables[i + 1:]:
                bt = b.get(Transform)
                bc = b.get(BoxCollider)
                bx = bt.x + bc.offset_x
                by = bt.y + bc.offset_y

                if not _aabb(ax, ay, ac.width, ac.height, bx, by, bc.width, bc.height):
                    continue

                # Fire callbacks on both sides
                self._fire(a, b, scene)
                self._fire(b, a, scene)

    def _fire(self, entity, other, scene) -> None:
        script = entity.try_get(Script)
        if script and script._on_collision:
            try:
                script._on_collision(entity, other, scene)
            except Exception:
                scene._errors.append({
                    "fn": f"Script({script.path}).on_collision",
                    "traceback": traceback.format_exc(),
                })
