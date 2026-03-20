"""Nimbus — agent-friendly 2D game engine."""

from nimbus.core.entity import Entity
from nimbus.core.scene import Scene
from nimbus.core.component import Component
from nimbus.input import Input

# Components
from nimbus.components.transform import Transform
from nimbus.components.rect_renderer import RectRenderer
from nimbus.components.sprite_renderer import SpriteRenderer
from nimbus.components.physics_body import PhysicsBody
from nimbus.components.box_collider import BoxCollider
from nimbus.components.script import Script
from nimbus.components.tag import Tag

__all__ = [
    "Entity", "Scene", "Component", "Input",
    "Transform", "RectRenderer", "SpriteRenderer",
    "PhysicsBody", "BoxCollider", "Script", "Tag",
]
