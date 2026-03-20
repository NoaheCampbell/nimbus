"""Player Movement — keyboard-controlled character example.

Load with:
    POST /scripts/load  {"path": "examples/player_movement.py"}
    POST /scene/start

Arrow keys move the player. Hold Shift to sprint.
"""

from nimbus import Entity, Input, Scene


class Player(Entity):
    def __init__(self):
        super().__init__(
            x=384, y=284,
            width=32, height=32,
            color=(80, 160, 255),
            tags={"player"},
        )
        self.speed = 200       # px/sec
        self.sprint_mult = 2.0

    def update(self, dt: float) -> None:
        multiplier = self.sprint_mult if Input.key_held("lshift") else 1.0
        vel = self.speed * multiplier * dt

        if Input.key_held("right"):
            self.x += vel
        if Input.key_held("left"):
            self.x -= vel
        if Input.key_held("up"):
            self.y -= vel
        if Input.key_held("down"):
            self.y += vel

        # Clamp to window bounds
        if self._scene:
            self.x = max(0, min(self._scene.width  - self.width,  self.x))
            self.y = max(0, min(self._scene.height - self.height, self.y))


class Wall(Entity):
    """A static obstacle."""
    def __init__(self, x, y, w, h):
        super().__init__(x=x, y=y, width=w, height=h, color=(160, 100, 60), tags={"wall"})


scene = Scene(name="player_movement", bgcolor=(30, 30, 30), width=800, height=600)

scene.add(Player())

# Some walls to bump into
scene.add(Wall(200, 150, 20, 200))
scene.add(Wall(400, 100, 200, 20))
scene.add(Wall(550, 300, 20, 200))
