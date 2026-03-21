from nimbus.core.component import Component


class Tag(Component):
    """Arbitrary string labels for grouping and querying entities."""

    def __init__(self, *labels: str) -> None:
        self.labels: set[str] = set(labels)

    def has(self, label: str) -> bool:
        return label in self.labels

    def to_dict(self) -> dict:
        return {"type": "Tag", "labels": sorted(self.labels)}
