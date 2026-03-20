"""Player script — hot-reloadable movement logic.

This file is watched for changes. Edit it while the game is running
and it will reload automatically on the next frame.
"""

from nimbus import Input, PhysicsBody, Transform


SPEED = 200
SPRINT_MULT = 2.0


def start(entity, scene):
    print(f"[player_script] start — entity: {entity.name}")


def update(entity, scene, dt):
    body = entity.get(PhysicsBody)
    t    = entity.get(Transform)
    mult = SPRINT_MULT if Input.key_held("lshift") else 1.0
    vel  = SPEED * mult

    body.velocity_x = 0
    body.velocity_y = 0

    if Input.key_held("right"): body.velocity_x =  vel
    if Input.key_held("left"):  body.velocity_x = -vel
    if Input.key_held("up"):    body.velocity_y = -vel
    if Input.key_held("down"):  body.velocity_y =  vel

    # Clamp to window
    from nimbus import RectRenderer
    rr = entity.try_get(RectRenderer)
    if rr and scene:
        t.x = max(0, min(scene.width  - rr.width,  t.x))
        t.y = max(0, min(scene.height - rr.height, t.y))


def on_collision(entity, other, scene):
    from nimbus import Tag
    tag = other.try_get(Tag)
    if tag and tag.has("wall"):
        # Push back out of the wall (simple — just stop velocity)
        body = entity.get(PhysicsBody)
        body.velocity_x = 0
        body.velocity_y = 0
