"""FastAPI control server — agents interact with the engine through here."""

from __future__ import annotations

import base64
import importlib.util
import sys
import threading
import traceback
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Engine instance is injected at startup
_engine = None


def get_engine():
    if _engine is None:
        raise RuntimeError("Engine not initialised")
    return _engine


app = FastAPI(
    title="Nimbus Agent API",
    description="HTTP control interface for the Nimbus 2D game engine.",
    version="0.1.0",
)


# ---------------------------------------------------------------------------
# Request/response models
# ---------------------------------------------------------------------------

class SceneConfig(BaseModel):
    name: str = "default"
    bgcolor: list[int] = [0, 0, 0]
    width: int = 800
    height: int = 600


class ScriptLoad(BaseModel):
    path: str                  # Absolute or relative path to the .py script
    scene_var: str = "scene"   # Name of the Scene variable exported by the script


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/", summary="Health check")
def root():
    """Returns engine status."""
    engine = get_engine()
    return {
        "status": "ok",
        "running": engine.is_running,
        "paused": engine.is_paused,
        "scene": engine.get_scene().name if engine.get_scene() else None,
    }


@app.post("/scene/load", summary="Load a scene from config")
def scene_load(config: SceneConfig):
    """Create a new blank scene from the given config and load it into the engine."""
    from nimbus.scene import Scene
    engine = get_engine()
    scene = Scene(
        name=config.name,
        bgcolor=tuple(config.bgcolor),  # type: ignore[arg-type]
        width=config.width,
        height=config.height,
    )
    engine.load_scene(scene)
    return {"loaded": scene.name}


@app.post("/scene/start", summary="Resume / unpause the scene")
def scene_start():
    engine = get_engine()
    engine.resume()
    return {"status": "running"}


@app.post("/scene/stop", summary="Pause the scene")
def scene_stop():
    engine = get_engine()
    engine.pause()
    return {"status": "paused"}


@app.post("/scripts/load", summary="Load an agent script into the engine")
def scripts_load(payload: ScriptLoad):
    """
    Dynamically import a Python script and extract a Scene from it.

    The script should define (and optionally populate) a `Scene` instance
    assigned to a module-level variable (default name: ``scene``).

    Example script::

        from nimbus import Scene, Entity

        class Ball(Entity):
            def update(self, dt):
                self.x += 200 * dt

        scene = Scene(name="bouncing")
        scene.add(Ball(x=50, y=50, width=24, height=24, color=(255, 80, 80)))

    The loaded scene is immediately set as the active scene.
    """
    script_path = Path(payload.path).resolve()
    if not script_path.exists():
        raise HTTPException(status_code=404, detail=f"Script not found: {script_path}")

    try:
        spec = importlib.util.spec_from_file_location("_nimbus_user_script", script_path)
        module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    except Exception:
        raise HTTPException(
            status_code=400,
            detail=f"Script error:\n{traceback.format_exc()}",
        )

    scene = getattr(module, payload.scene_var, None)
    if scene is None:
        raise HTTPException(
            status_code=400,
            detail=f"Script did not define a variable named '{payload.scene_var}'.",
        )

    from nimbus.scene import Scene as SceneClass
    if not isinstance(scene, SceneClass):
        raise HTTPException(
            status_code=400,
            detail=f"'{payload.scene_var}' is not a Scene instance.",
        )

    engine = get_engine()
    engine.load_scene(scene)
    return {"loaded": scene.name, "entities": len(scene.entities)}


@app.get("/state", summary="Get current game state as JSON")
def state():
    """Returns the full scene state: entity positions, properties, etc."""
    engine = get_engine()
    scene = engine.get_scene()
    if scene is None:
        return {"scene": None}
    return {"scene": scene.to_dict()}


@app.get("/screenshot", summary="Capture current frame as base64 PNG")
def screenshot():
    """
    Captures the game window and returns the image as a base64-encoded PNG.

    Agents with vision capability can decode and inspect this to understand
    what is currently visible in the game.
    """
    engine = get_engine()
    png_bytes = engine.screenshot()
    if png_bytes is None:
        raise HTTPException(status_code=503, detail="Engine window not ready yet.")
    encoded = base64.b64encode(png_bytes).decode("utf-8")
    return {"format": "png", "encoding": "base64", "data": encoded}


@app.get("/video", summary="Capture a short gameplay video as base64 GIF")
def video(duration: float = 2.0, fps: int = 15):
    """
    Records the game for `duration` seconds at `fps` frames per second and
    returns an animated GIF as a base64-encoded string.

    Parameters:
    - **duration**: Recording length in seconds (max 10, default 2)
    - **fps**: Capture frame rate (max 30, default 30)

    The GIF can be decoded and displayed directly by the caller, or passed
    to a vision model to understand motion and game behaviour over time.
    """
    import io
    import time
    from PIL import Image

    duration = min(max(duration, 0.1), 10.0)
    fps = min(max(fps, 1), 30)

    engine = get_engine()
    if not engine.is_running:
        raise HTTPException(status_code=503, detail="Engine window not ready yet.")

    frame_interval = 1.0 / fps
    frames: list[Image.Image] = []
    deadline = time.monotonic() + duration

    while time.monotonic() < deadline:
        frame_start = time.monotonic()
        png_bytes = engine.screenshot()
        if png_bytes:
            frames.append(Image.open(io.BytesIO(png_bytes)).convert("RGB"))
        elapsed = time.monotonic() - frame_start
        sleep_for = frame_interval - elapsed
        if sleep_for > 0:
            time.sleep(sleep_for)

    if not frames:
        raise HTTPException(status_code=503, detail="No frames captured.")

    buf = io.BytesIO()
    frames[0].save(
        buf,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=int(1000 / fps),  # ms per frame
        loop=0,
    )
    encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
    return {
        "format": "gif",
        "encoding": "base64",
        "frames": len(frames),
        "duration": duration,
        "fps": fps,
        "data": encoded,
    }


# ---------------------------------------------------------------------------
# Server startup helper
# ---------------------------------------------------------------------------

def start_server(engine, host: str = "127.0.0.1", port: int = 8765) -> threading.Thread:
    """Inject the engine and start uvicorn on a daemon thread."""
    global _engine
    _engine = engine

    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True, name="nimbus-api")
    thread.start()
    return thread
