from nimbus.core.component import Component


class BoxCollider(Component):
    """Axis-aligned bounding box collider."""

    def __init__(
        self,
        width: int = 32,
        height: int = 32,
        offset_x: float = 0,
        offset_y: float = 0,
        is_trigger: bool = False,   # trigger = detects overlap but no physics response
    ) -> None:
        self.width = width
        self.height = height
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.is_trigger = is_trigger
