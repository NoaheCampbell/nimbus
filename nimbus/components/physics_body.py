from nimbus.core.component import Component


class PhysicsBody(Component):
    """Simple 2D physics — velocity, gravity, drag. No external library needed."""

    def __init__(
        self,
        velocity_x: float = 0,
        velocity_y: float = 0,
        gravity: float = 0,         # pixels/sec² downward (0 = disabled)
        drag: float = 0,            # velocity multiplier per second (0 = no drag)
        mass: float = 1.0,
        kinematic: bool = False,    # if True, not affected by physics systems
    ) -> None:
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.gravity = gravity
        self.drag = drag
        self.mass = mass
        self.kinematic = kinematic

    def apply_force(self, fx: float, fy: float) -> None:
        """Apply a force (F = ma → a = F/m → add to velocity this frame)."""
        self.velocity_x += fx / self.mass
        self.velocity_y += fy / self.mass
