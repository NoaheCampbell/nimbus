from nimbus.core.component import Component


class SpriteRenderer(Component):
    """Renders an image. Uses Transform for position/scale/rotation."""

    def __init__(
        self,
        image: str = "",
        layer: int = 0,
        flip_x: bool = False,
        flip_y: bool = False,
        opacity: float = 1.0,
        visible: bool = True,
    ) -> None:
        self.image = image          # path to image file
        self.layer = layer
        self.flip_x = flip_x
        self.flip_y = flip_y
        self.opacity = opacity      # 0.0 - 1.0
        self.visible = visible
        self._surface_cache = None  # internal, not serialised
