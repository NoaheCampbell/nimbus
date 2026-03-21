"""Bouncing Ball — ECS version.

Load with:
    POST /scripts/load  {"path": "examples/bouncing_ball.py"}
    POST /scene/start
"""

from nimbus import Scene, Entity, Transform, RectRenderer, PhysicsBody, Script, Tag


BALL_SPEED = 250  # px/sec


def make_ball(name, x, y, color, vx, vy):
    e = Entity(name=name)
    e.add(Transform(x=x, y=y))
    e.add(RectRenderer(width=24, height=24, color=color))
    e.add(PhysicsBody(velocity_x=vx, velocity_y=vy))
    e.add(Tag("ball"))
    return e


class BouncingBallScene(Scene):
    def on_load(self):
        self.add(make_ball("ball_red",   100, 100, (255,  80,  80),  BALL_SPEED, 180))
        self.add(make_ball("ball_blue",  400, 300, ( 80, 160, 255), -200,  220))
        self.add(make_ball("ball_green", 600, 150, ( 80, 255, 140),  180, -240))

    def update(self, dt):
        super().update(dt)
        # Bounce balls off walls
        for entity in self.query(Transform, PhysicsBody, RectRenderer):
            t   = entity.get(Transform)
            b   = entity.get(PhysicsBody)
            rr  = entity.get(RectRenderer)
            right  = self.width  - rr.width
            bottom = self.height - rr.height

            if t.x <= 0:        t.x = 0;      b.velocity_x =  abs(b.velocity_x)
            elif t.x >= right:  t.x = right;  b.velocity_x = -abs(b.velocity_x)
            if t.y <= 0:        t.y = 0;      b.velocity_y =  abs(b.velocity_y)
            elif t.y >= bottom: t.y = bottom; b.velocity_y = -abs(b.velocity_y)


scene = BouncingBallScene(name="bouncing_ball", bgcolor=(15, 15, 25), width=800, height=600)
