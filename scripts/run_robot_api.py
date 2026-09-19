#!/usr/bin/env python3
"""Run the provisional robot HTTP API with a mock backend only."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.gitirl_agent.robot.http_server import RobotHTTPServer
from src.gitirl_agent.robot.mock import MockRobotAdapter
from src.gitirl_agent.state.models import ObjectState, WorldState


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mock",
        action="store_true",
        help="required; real robot execution must be supplied by Ryan/Sarah",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    arguments = parser.parse_args()
    if not arguments.mock:
        raise SystemExit("Only --mock is implemented; no real robot behavior is guessed")

    current = WorldState(
        objects=(ObjectState("box_A", label="box", position="Y"),)
    )
    server = RobotHTTPServer(
        MockRobotAdapter(current),
        host=arguments.host,
        port=arguments.port,
        token=os.environ.get("GITIRL_ROBOT_TOKEN") or None,
    )
    print(f"mock robot API: {server.base_url}")
    print("Ctrl-C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
