"""PhysicsSystem — applies velocity, gravity, and drag."""

from nimbus.core.system import System
from nimbus.components.transform import Transform
from nimbus.components.physics_body import PhysicsBody


class PhysicsSystem(System):
    def update(self, dt: float, scene) -> None:
        for entity in scene.query(Transform, PhysicsBody):
            t = entity.get(Transform)
            body = entity.get(PhysicsBody)

            if body.kinematic:
                continue

            # Gravity
            if body.gravity:
                body.velocity_y += body.gravity * dt

            # Drag
            if body.drag:
                factor = max(0.0, 1.0 - body.drag * dt)
                body.velocity_x *= factor
                body.velocity_y *= factor

            # Integrate
            t.x += body.velocity_x * dt
            t.y += body.velocity_y * dt
