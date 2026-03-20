"""Platformer demo — gravity, jumping, platforms, collectible coins.

Load with:
    POST /scripts/load  {"path": "examples/platformer.py"}
    POST /scene/start

Controls: Arrow keys to move, Space to jump.

Demonstrates:
- Gravity + physics
- Platform collision with solid response
- Collectible entities (coins)
- Score tracked in scene state
- Custom background (gradient sky)
- Layered rendering
"""

import pygame
from nimbus import (
    Scene, Entity, Transform, RectRenderer,
    PhysicsBody, BoxCollider, Tag, Input
)


# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------

class PlatformerScene(Scene):

    def on_load(self):
        self.score = 0
        self.coins_remaining = 0

        self._build_world()

    def _build_world(self):
        W, H = self.width, self.height

        # -- Player --
        player = Entity(name="player")
        player.add(Transform(x=80, y=H - 120))
        player.add(RectRenderer(width=28, height=36, color=(80, 160, 255), layer=2))
        player.add(PhysicsBody(gravity=1200, drag=0))
        player.add(BoxCollider(width=28, height=36))
        player.add(Tag("player"))
        self.add(player)

        # -- Ground --
        self._platform("ground", 0, H - 32, W, 32, (80, 60, 40))

        # -- Platforms --
        platforms = [
            (120,  H - 130, 160, 18),
            (340,  H - 200, 140, 18),
            (520,  H - 160, 120, 18),
            (160,  H - 290, 180, 18),
            (460,  H - 310, 160, 18),
            (280,  H - 390, 140, 18),
            (520,  H - 440, 180, 18),
            (80,   H - 460, 120, 18),
            (320,  H - 510, 200, 18),
        ]
        for i, (x, y, w, h) in enumerate(platforms):
            shade = max(40, 110 - i * 8)
            self._platform(f"platform_{i}", x, y, w, h, (shade, int(shade*0.8), shade//2))

        # -- Coins on platforms --
        coin_positions = [
            (160,  H - 160),
            (200,  H - 160),
            (240,  H - 160),
            (380,  H - 230),
            (420,  H - 230),
            (200,  H - 320),
            (240,  H - 320),
            (280,  H - 320),
            (500,  H - 340),
            (540,  H - 340),
            (350,  H - 420),
            (390,  H - 420),
            (560,  H - 470),
            (600,  H - 470),
            (360,  H - 540),
            (400,  H - 540),
            (440,  H - 540),
        ]
        for i, (cx, cy) in enumerate(coin_positions):
            coin = Entity(name=f"coin_{i}")
            coin.add(Transform(x=cx, y=cy))
            coin.add(RectRenderer(width=12, height=12, color=(255, 215, 0), layer=2))
            coin.add(BoxCollider(width=12, height=12, is_trigger=True))
            coin.add(Tag("coin"))
            self.add(coin)
            self.coins_remaining += 1

    def _platform(self, name, x, y, w, h, color):
        e = Entity(name=name)
        e.add(Transform(x=x, y=y))
        e.add(RectRenderer(width=w, height=h, color=color, layer=1))
        e.add(BoxCollider(width=w, height=h))
        e.add(Tag("solid"))
        self.add(e)
        return e

    def draw_background(self, screen):
        """Gradient sky — dark blue at top, lighter at horizon."""
        H = self.height
        W = self.width
        for y in range(H):
            t = y / H
            r = int(10  + t * 40)
            g = int(10  + t * 50)
            b = int(40  + t * 80)
            pygame.draw.line(screen, (r, g, b), (0, y), (W, y))

        # Simple stars in upper half
        import hashlib
        for i in range(60):
            h = int(hashlib.md5(f"star{i}".encode()).hexdigest(), 16)
            sx = (h >> 16) % W
            sy = (h & 0xFFFF) % (H // 2)
            brightness = 150 + (h % 100)
            pygame.draw.rect(screen, (brightness, brightness, brightness), (sx, sy, 2, 2))

    def update(self, dt):
        super().update(dt)

        player_entity = self.find("player")
        if not player_entity:
            return

        pt = player_entity.get(Transform)
        pb = player_entity.get(PhysicsBody)
        pc = player_entity.get(BoxCollider)

        # -- Player input --
        speed = 220
        pb.velocity_x = 0
        if Input.key_held("right"): pb.velocity_x =  speed
        if Input.key_held("left"):  pb.velocity_x = -speed

        # -- Platform collision (solid response) --
        on_ground = False
        player_rect = (pt.x, pt.y, pc.width, pc.height)

        for entity in self.query(BoxCollider, Tag):
            tag = entity.get(Tag)
            if not tag.has("solid"):
                continue
            et = entity.get(Transform)
            ec = entity.get(BoxCollider)

            px, py, pw, ph = player_rect
            ex, ey, ew, eh = et.x + ec.offset_x, et.y + ec.offset_y, ec.width, ec.height

            # AABB overlap
            if not (px < ex + ew and px + pw > ex and py < ey + eh and py + ph > ey):
                continue

            # Resolve: find smallest penetration axis
            overlap_x = min(px + pw - ex, ex + ew - px)
            overlap_y = min(py + ph - ey, ey + eh - py)

            if overlap_y < overlap_x:
                if py + ph / 2 < ey + eh / 2:
                    pt.y = ey - ph
                    on_ground = True
                    if pb.velocity_y > 0:
                        pb.velocity_y = 0
                else:
                    pt.y = ey + eh
                    if pb.velocity_y < 0:
                        pb.velocity_y = 0
            else:
                if px + pw / 2 < ex + ew / 2:
                    pt.x = ex - pw
                else:
                    pt.x = ex + ew
                pb.velocity_x = 0

        # -- Jump --
        if on_ground and Input.key_pressed("space"):
            pb.velocity_y = -620

        # -- Coin collection --
        collected = []
        for entity in self.query(Transform, BoxCollider, Tag):
            tag = entity.get(Tag)
            if not tag.has("coin"):
                continue
            ct = entity.get(Transform)
            cc = entity.get(BoxCollider)
            px, py, pw, ph = pt.x, pt.y, pc.width, pc.height
            cx2, cy2, cw, ch = ct.x, ct.y, cc.width, cc.height
            if px < cx2 + cw and px + pw > cx2 and py < cy2 + ch and py + ph > cy2:
                collected.append(entity)

        for coin in collected:
            self.score += 1
            self.coins_remaining -= 1
            self.destroy(coin)

        # -- Clamp to world bounds --
        pt.x = max(0, min(self.width - pc.width, pt.x))
        if pt.y > self.height:
            pt.y = self.height - 200
            pb.velocity_y = 0

    def to_dict(self):
        d = super().to_dict()
        d["score"] = self.score
        d["coins_remaining"] = self.coins_remaining
        return d


scene = PlatformerScene(
    name="platformer",
    bgcolor=(10, 10, 40),
    width=800,
    height=600,
)
