"""Player Movement — ECS + Script component version.

Load with:
    POST /scripts/load  {"path": "examples/player_movement.py"}
    POST /scene/start

Arrow keys move the player. Hold Shift to sprint.
"""

from nimbus import (
    Scene, Entity, Transform, RectRenderer,
    PhysicsBody, BoxCollider, Script, Tag
)
import os

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "player_script.py")


class PlayerMovementScene(Scene):
    def on_load(self):
        # Player
        player = Entity(name="player")
        player.add(Transform(x=384, y=284))
        player.add(RectRenderer(width=32, height=32, color=(80, 160, 255)))
        player.add(PhysicsBody())
        player.add(BoxCollider(width=32, height=32))
        player.add(Script(SCRIPT_PATH))
        player.add(Tag("player"))
        self.add(player)

        # Walls
        for name, x, y, w, h in [
            ("wall1", 200, 150, 20, 200),
            ("wall2", 400, 100, 200, 20),
            ("wall3", 550, 300, 20, 200),
        ]:
            wall = Entity(name=name)
            wall.add(Transform(x=x, y=y))
            wall.add(RectRenderer(width=w, height=h, color=(160, 100, 60)))
            wall.add(BoxCollider(width=w, height=h))
            wall.add(Tag("wall"))
            self.add(wall)


scene = PlayerMovementScene(name="player_movement", bgcolor=(30, 30, 30))
