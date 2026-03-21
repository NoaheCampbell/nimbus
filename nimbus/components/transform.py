from nimbus.core.component import Component


class Transform(Component):
    """Position, rotation, and scale in 2D world space."""

    def __init__(
        self,
        x: float = 0,
        y: float = 0,
        rotation: float = 0,
        scale_x: float = 1.0,
        scale_y: float = 1.0,
    ) -> None:
        self.x = x
        self.y = y
        self.rotation = rotation    # degrees
        self.scale_x = scale_x
        self.scale_y = scale_y
