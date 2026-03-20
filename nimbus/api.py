"""FastAPI control server — the agent's eyes, hands, and inspector."""

from __future__ import annotations

import base64
import importlib.util
import threading
import traceback
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

_engine = None


def get_engine():
    if _engine is None:
        raise RuntimeError("Engine not initialised")
    return _engine


app = FastAPI(
    title="Nimbus Agent API",
    description="HTTP control interface for the Nimbus 2D game engine.",
    version="0.2.0",
)


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class ScriptLoad(BaseModel):
    path: str
    scene_var: str = "scene"

class AssertionsPayload(BaseModel):
    assertions: list[dict]

class EntityCreate(BaseModel):
    name: str = ""

class ComponentAdd(BaseModel):
    type: str
    props: dict = {}

class ComponentUpdate(BaseModel):
    props: dict


# ---------------------------------------------------------------------------
# Status & control
# ---------------------------------------------------------------------------

@app.get("/", summary="Engine status")
def root():
    engine = get_engine()
    scene = engine.get_scene()
    return {
        "status": "ok",
        "running": engine.is_running,
        "paused": engine.is_paused,
        "scene": scene.name if scene else None,
    }


@app.post("/scene/start", summary="Resume / unpause")
def scene_start():
    get_engine().resume()
    return {"status": "running"}


@app.post("/scene/stop", summary="Pause")
def scene_stop():
    get_engine().pause()
    return {"status": "paused"}


@app.post("/scripts/load", summary="Load a scene script")
def scripts_load(payload: ScriptLoad):
    """
    Dynamically import a Python script and extract a Scene from it.

    The script should assign a Scene subclass instance to a module-level
    variable (default name: ``scene``).

    Example::

        from nimbus.core.scene import Scene
        from nimbus.core.entity import Entity
        from nimbus.components.transform import Transform
        from nimbus.components.rect_renderer import RectRenderer

        class MyScene(Scene):
            def on_load(self):
                player = Entity(name="player")
                player.add(Transform(x=100, y=100))
                player.add(RectRenderer(width=32, height=32, color=(0, 120, 255)))
                self.add(player)

        scene = MyScene(name="my_game")
    """
    script_path = Path(payload.path).resolve()
    if not script_path.exists():
        raise HTTPException(status_code=404, detail=f"Script not found: {script_path}")

    try:
        spec = importlib.util.spec_from_file_location("_nimbus_user_scene", script_path)
        module = importlib.util.module_from_spec(spec)   # type: ignore[arg-type]
        spec.loader.exec_module(module)                   # type: ignore[union-attr]
    except Exception:
        raise HTTPException(status_code=400, detail=f"Script error:\n{traceback.format_exc()}")

    scene = getattr(module, payload.scene_var, None)
    if scene is None:
        raise HTTPException(status_code=400,
            detail=f"Script did not define a variable named '{payload.scene_var}'.")

    from nimbus.core.scene import Scene as SceneClass
    if not isinstance(scene, SceneClass):
        raise HTTPException(status_code=400,
            detail=f"'{payload.scene_var}' is not a Scene instance.")

    get_engine().load_scene(scene)
    return {"loaded": scene.name}


# ---------------------------------------------------------------------------
# State & observation
# ---------------------------------------------------------------------------

@app.get("/state", summary="Full scene state as JSON")
def state():
    engine = get_engine()
    scene = engine.get_scene()
    if scene is None:
        return {"scene": None}
    return {"scene": scene.to_dict()}


@app.get("/errors", summary="Get and clear runtime errors")
def errors():
    """Returns all runtime errors captured since last call, then clears them.
    Errors include script exceptions, bad component calls, etc."""
    engine = get_engine()
    scene = engine.get_scene()
    if scene is None:
        return {"errors": []}
    return {"errors": scene.pop_errors()}


@app.get("/screenshot", summary="Current frame as base64 PNG")
def screenshot():
    engine = get_engine()
    png = engine.screenshot()
    if png is None:
        raise HTTPException(status_code=503, detail="Engine window not ready.")
    return {"format": "png", "encoding": "base64", "data": base64.b64encode(png).decode()}


@app.get("/video", summary="Record gameplay as base64 GIF")
def video(duration: float = 2.0, fps: int = 15):
    """Records the game for `duration` seconds (max 10) at `fps` fps (max 30)."""
    import io, time
    from PIL import Image

    duration = min(max(duration, 0.1), 10.0)
    fps = min(max(fps, 1), 30)

    engine = get_engine()
    if not engine.is_running:
        raise HTTPException(status_code=503, detail="Engine not running.")

    interval = 1.0 / fps
    frames: list[Image.Image] = []
    deadline = time.monotonic() + duration

    while time.monotonic() < deadline:
        t0 = time.monotonic()
        png = engine.screenshot()
        if png:
            frames.append(Image.open(io.BytesIO(png)).convert("RGB"))
        sleep = interval - (time.monotonic() - t0)
        if sleep > 0:
            time.sleep(sleep)

    if not frames:
        raise HTTPException(status_code=503, detail="No frames captured.")

    buf = io.BytesIO()
    frames[0].save(buf, format="GIF", save_all=True, append_images=frames[1:],
                   duration=int(1000 / fps), loop=0)
    return {
        "format": "gif", "encoding": "base64",
        "frames": len(frames), "duration": duration, "fps": fps,
        "data": base64.b64encode(buf.getvalue()).decode(),
    }


# ---------------------------------------------------------------------------
# Behavioral assertions
# ---------------------------------------------------------------------------

@app.post("/assert", summary="Run behavioral assertions against scene state")
def assert_scene(payload: AssertionsPayload):
    """
    Verify game state without vision. Returns structured pass/fail results.

    Example payload::

        {
          "assertions": [
            {"entity": "player", "op": "exists"},
            {"entity": "player", "component": "Transform", "field": "x", "op": "near", "value": 100, "tolerance": 10},
            {"entity": "player", "component": "PhysicsBody", "field": "velocity_y", "op": "less_than", "value": 0}
          ]
        }

    Supported ops: exists, equals, near, greater_than, less_than, between (requires lo+hi)
    """
    scene = get_engine().get_scene()
    if scene is None:
        raise HTTPException(status_code=503, detail="No scene loaded.")
    from nimbus.core.assertions import SceneAssertions
    return SceneAssertions(scene).run(payload.assertions)


# ---------------------------------------------------------------------------
# Entity management
# ---------------------------------------------------------------------------

@app.post("/entity/create", summary="Create a new entity")
def entity_create(payload: EntityCreate):
    scene = get_engine().get_scene()
    if scene is None:
        raise HTTPException(status_code=503, detail="No scene loaded.")
    from nimbus.core.entity import Entity
    e = Entity(name=payload.name)
    scene.add(e)
    return {"id": e.id, "name": e.name}


@app.delete("/entity/{entity_id}", summary="Destroy an entity")
def entity_destroy(entity_id: str):
    scene = get_engine().get_scene()
    if scene is None:
        raise HTTPException(status_code=503, detail="No scene loaded.")
    entity = scene.get(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found.")
    scene.destroy(entity)
    return {"destroyed": entity_id}


@app.get("/entity/{entity_id}", summary="Get entity state")
def entity_get(entity_id: str):
    scene = get_engine().get_scene()
    if scene is None:
        raise HTTPException(status_code=503, detail="No scene loaded.")
    entity = scene.get(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found.")
    return entity.to_dict()


@app.post("/entity/{entity_id}/component", summary="Add or replace a component")
def component_add(entity_id: str, payload: ComponentAdd):
    """Add a component to an entity by type name. Replaces if already present.

    Example: {"type": "Transform", "props": {"x": 100, "y": 200}}

    Supported types: Transform, RectRenderer, SpriteRenderer, PhysicsBody, BoxCollider, Tag
    """
    scene = get_engine().get_scene()
    if scene is None:
        raise HTTPException(status_code=503, detail="No scene loaded.")
    entity = scene.get(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found.")

    comp = _build_component(payload.type, payload.props)
    entity.add(comp)
    return {"added": payload.type, "entity": entity_id}


@app.put("/entity/{entity_id}/component/{component_type}", summary="Update component properties")
def component_update(entity_id: str, component_type: str, payload: ComponentUpdate):
    scene = get_engine().get_scene()
    if scene is None:
        raise HTTPException(status_code=503, detail="No scene loaded.")
    entity = scene.get(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found.")

    comp = _find_component_by_name(entity, component_type)
    if comp is None:
        raise HTTPException(status_code=404, detail=f"Component '{component_type}' not found.")

    for key, val in payload.props.items():
        if hasattr(comp, key):
            setattr(comp, key, val)
    return {"updated": component_type, "props": payload.props}


@app.delete("/entity/{entity_id}/component/{component_type}", summary="Remove a component")
def component_remove(entity_id: str, component_type: str):
    scene = get_engine().get_scene()
    if scene is None:
        raise HTTPException(status_code=503, detail="No scene loaded.")
    entity = scene.get(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found.")

    comp = _find_component_by_name(entity, component_type)
    if comp is None:
        raise HTTPException(status_code=404, detail=f"Component '{component_type}' not found.")

    entity.remove(type(comp))
    return {"removed": component_type}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_COMPONENT_REGISTRY = {}

def _register_components():
    from nimbus.components.transform import Transform
    from nimbus.components.rect_renderer import RectRenderer
    from nimbus.components.sprite_renderer import SpriteRenderer
    from nimbus.components.physics_body import PhysicsBody
    from nimbus.components.box_collider import BoxCollider
    from nimbus.components.tag import Tag
    from nimbus.components.script import Script
    for cls in [Transform, RectRenderer, SpriteRenderer, PhysicsBody, BoxCollider, Tag, Script]:
        _COMPONENT_REGISTRY[cls.__name__] = cls

_register_components()


def _build_component(type_name: str, props: dict):
    cls = _COMPONENT_REGISTRY.get(type_name)
    if cls is None:
        raise HTTPException(status_code=400, detail=f"Unknown component type: '{type_name}'")
    try:
        obj = cls()
        for k, v in props.items():
            if hasattr(obj, k):
                setattr(obj, k, v)
        return obj
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not build {type_name}: {e}")


def _find_component_by_name(entity, name: str):
    for comp in entity.all_components():
        if type(comp).__name__ == name:
            return comp
    return None


# ---------------------------------------------------------------------------
# Server startup
# ---------------------------------------------------------------------------

def start_server(engine, host: str = "127.0.0.1", port: int = 8765) -> threading.Thread:
    global _engine
    _engine = engine
    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True, name="nimbus-api")
    thread.start()
    return thread
