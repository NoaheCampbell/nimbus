from nimbus.core.component import Component


class RectRenderer(Component):
    """Renders a solid colored rectangle. Uses Transform for position."""

    def __init__(
        self,
        width: int = 32,
        height: int = 32,
        color: tuple = (255, 255, 255),
        layer: int = 0,
        visible: bool = True,
    ) -> None:
        self.width = width
        self.height = height
        self.color = list(color)
        self.layer = layer
        self.visible = visible
