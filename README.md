# 🌥 Nimbus

A 2D game engine designed for **autonomous agent development**. Agents write Python scripts, load them via HTTP API, and observe the results through a screenshot endpoint — no GUI editor required.

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start the engine
python main.py
```

The game window opens and the API server starts on `http://127.0.0.1:8765`.

API docs (Swagger UI): `http://127.0.0.1:8765/docs`

---

## Agent Workflow

```
1. Write a scene script  →  2. POST /scripts/load  →  3. POST /scene/start
                                                      ↓
                         ←  iterate & fix  ←  GET /screenshot
```

### Step 1 — Write a script

```python
# my_game.py
from nimbus import Entity, Scene, Input

class Player(Entity):
    def __init__(self):
        super().__init__(x=100, y=100, width=32, height=32, color=(0, 120, 255))
        self.speed = 200

    def update(self, dt):
        if Input.key_held("right"):
            self.x += self.speed * dt
        if Input.key_held("left"):
            self.x -= self.speed * dt

scene = Scene(name="my_game", bgcolor=(20, 20, 30))
scene.add(Player())
```

### Step 2 — Load it

```bash
curl -X POST http://127.0.0.1:8765/scripts/load \
     -H "Content-Type: application/json" \
     -d '{"path": "/path/to/my_game.py"}'
```

### Step 3 — Start it

```bash
curl -X POST http://127.0.0.1:8765/scene/start
```

### Step 4 — See what's happening

```bash
curl http://127.0.0.1:8765/screenshot
# Returns {"format": "png", "encoding": "base64", "data": "..."}
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/` | Engine status (running, paused, current scene) |
| `POST` | `/scene/load` | Create & load a blank scene from config JSON |
| `POST` | `/scene/start` | Resume / unpause the running scene |
| `POST` | `/scene/stop` | Pause the scene |
| `POST` | `/scripts/load` | Load a Python script; extract and activate its `scene` |
| `GET`  | `/state` | Full scene state as JSON (entities, positions, properties) |
| `GET`  | `/screenshot` | Current frame as base64-encoded PNG |

### `POST /scene/load`
```json
{
  "name": "level1",
  "bgcolor": [20, 20, 30],
  "width": 800,
  "height": 600
}
```

### `POST /scripts/load`
```json
{
  "path": "examples/bouncing_ball.py",
  "scene_var": "scene"
}
```
`scene_var` is the name of the `Scene` variable in the script (default: `"scene"`).

### `GET /state` response
```json
{
  "scene": {
    "name": "bouncing_ball",
    "bgcolor": [15, 15, 25],
    "width": 800,
    "height": 600,
    "entity_count": 3,
    "entities": [
      {"id": "a1b2c3", "type": "Ball", "x": 142.5, "y": 87.3, "width": 40, "height": 40, ...}
    ]
  }
}
```

---

## Scripting API

### `Entity`

Base class for all game objects.

```python
class Entity:
    x: float          # world position
    y: float
    width: int        # bounding box
    height: int
    color: tuple      # RGB, used when no sprite
    sprite: str|None  # path to image file
    visible: bool
    tags: set[str]    # arbitrary labels

    def update(self, dt: float): ...       # called every frame
    def on_event(self, event): ...         # receives pygame events
    def overlaps(self, other) -> bool: ... # AABB collision
    def find(self, tag: str) -> list: ...  # find entities by tag in same scene
    def destroy(self): ...                 # remove from scene
    def to_dict(self) -> dict: ...         # JSON-serialisable state
```

### `Scene`

Container for entities.

```python
scene = Scene(name="level1", bgcolor=(0,0,0), width=800, height=600)
scene.add(entity)
scene.remove(entity)
scene.clear()
```

### `Input`

Static input polling — no pygame imports needed in scripts.

```python
Input.key_held("right")       # True while key is down
Input.key_pressed("space")    # True only on first frame pressed
Input.key_released("space")   # True only on frame released
Input.mouse_pos()             # (x, y) tuple
Input.mouse_button(1)         # True while left mouse held

# Key names: "up", "down", "left", "right", "space", "return",
#            "escape", "lshift", "rshift", "tab", "a"-"z", "0"-"9"
```

---

## Examples

| File | Description |
|------|-------------|
| `examples/bouncing_ball.py` | Three colored balls bouncing around the window |
| `examples/player_movement.py` | Arrow-key controlled player with walls |

Load any example:
```bash
curl -X POST http://127.0.0.1:8765/scripts/load \
     -d '{"path": "examples/bouncing_ball.py"}'
curl -X POST http://127.0.0.1:8765/scene/start
```

---

## Command-Line Options

```
python main.py [--width W] [--height H] [--fps N] [--title TITLE]
               [--host HOST] [--port PORT]
```

Default: `800×600`, `60fps`, API on `127.0.0.1:8765`.
