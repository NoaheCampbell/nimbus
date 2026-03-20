"""Nimbus entry point — starts the API server and game engine together."""

import argparse
import time

from nimbus.engine import Engine
from nimbus.api import start_server


def main():
    parser = argparse.ArgumentParser(description="Nimbus 2D Game Engine")
    parser.add_argument("--width",  type=int, default=800,        help="Window width (default 800)")
    parser.add_argument("--height", type=int, default=600,        help="Window height (default 600)")
    parser.add_argument("--fps",    type=int, default=60,         help="Target FPS (default 60)")
    parser.add_argument("--title",  type=str, default="Nimbus",   help="Window title")
    parser.add_argument("--host",   type=str, default="127.0.0.1",help="API host (default 127.0.0.1)")
    parser.add_argument("--port",   type=int, default=8765,       help="API port (default 8765)")
    args = parser.parse_args()

    engine = Engine(
        width=args.width,
        height=args.height,
        title=args.title,
        fps=args.fps,
    )

    # Start the API server on a background thread
    api_thread = start_server(engine, host=args.host, port=args.port)
    time.sleep(0.5)  # brief pause so uvicorn is ready before the loop starts

    print(f"🌥  Nimbus running")
    print(f"   Window : {args.width}x{args.height} @ {args.fps}fps")
    print(f"   API    : http://{args.host}:{args.port}")
    print(f"   Docs   : http://{args.host}:{args.port}/docs")
    print()
    print("Load a scene via the API or pass a script:")
    print(f"  POST http://{args.host}:{args.port}/scripts/load  {{\"path\": \"examples/bouncing_ball.py\"}}")
    print()

    # This blocks until the window is closed
    engine.run()


if __name__ == "__main__":
    main()
