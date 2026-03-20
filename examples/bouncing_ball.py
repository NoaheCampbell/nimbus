"""Bouncing Ball — a simple example an agent might write.

Load this into Nimbus with:
    POST /scripts/load  {"path": "examples/bouncing_ball.py"}

Then start the scene:
    POST /scene/start

Then grab a screenshot to see what's happening:
    GET /screenshot
"""

from nimbus import Entity, Scene


class Ball(Entity):
    """A colored ball that bounces around the window."""

    def __init__(self, x=100, y=100, radius=20, color=(255, 80, 80), vx=250, vy=180):
        super().__init__(
            x=x,
            y=y,
            width=radius * 2,
            height=radius * 2,
            color=color,
        )
        self.vx = vx  # pixels per second
        self.vy = vy

    def update(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Bounce off walls (scene dimensions come through _scene)
        if self._scene:
            right  = self._scene.width  - self.width
            bottom = self._scene.height - self.height

            if self.x <= 0:
                self.x = 0
                self.vx = abs(self.vx)
            elif self.x >= right:
                self.x = right
                self.vx = -abs(self.vx)

            if self.y <= 0:
                self.y = 0
                self.vy = abs(self.vy)
            elif self.y >= bottom:
                self.y = bottom
                self.vy = -abs(self.vy)


# -- Scene definition (exported for /scripts/load) -------------------------
scene = Scene(name="bouncing_ball", bgcolor=(15, 15, 25), width=800, height=600)

scene.add(Ball(x=100, y=100, color=(255,  80,  80), vx=250, vy=180))
scene.add(Ball(x=400, y=300, color=( 80, 180, 255), vx=-200, vy=220))
scene.add(Ball(x=600, y=150, color=( 80, 255, 140), vx=180, vy=-240))
