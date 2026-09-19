#!/usr/bin/env python3
"""Stream three provisional camera byte streams to Daniel's WebSocket."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.gitirl_agent.media.camera_stream import (
    CameraWebSocketSender,
    LengthPrefixedFrameSource,
)


def parse_camera(value: str):
    try:
        camera_id, angle, raw_path = value.split(":", 2)
        return camera_id, float(angle), Path(raw_path)
    except (TypeError, ValueError) as error:
        raise argparse.ArgumentTypeError(
            "camera must use CAMERA_ID:ANGLE_DEGREES:PATH"
        ) from error


async def run(arguments: argparse.Namespace) -> None:
    url = os.environ.get("GITIRL_CAMERA_WS_URL")
    if not url:
        raise SystemExit("GITIRL_CAMERA_WS_URL must be set")

    camera_values = arguments.camera or [
        ("camera_0", 0.0, Path("/tmp/gitirl-camera-0.frames")),
        ("camera_1", 120.0, Path("/tmp/gitirl-camera-1.frames")),
        ("camera_2", 240.0, Path("/tmp/gitirl-camera-2.frames")),
    ]
    if len(camera_values) != 3:
        raise SystemExit("Exactly three --camera values are required")

    sources = {
        camera_id: LengthPrefixedFrameSource(
            camera_id=camera_id,
            mount_angle_degrees=angle,
            path=path,
            encoding=arguments.encoding,
        )
        for camera_id, angle, path in camera_values
    }
    if len(sources) != 3:
        raise SystemExit("Camera IDs must be unique")

    sender = CameraWebSocketSender(
        url=url,
        token=os.environ.get("GITIRL_CAMERA_WS_TOKEN"),
    )
    await sender.stream(sources)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--camera",
        action="append",
        type=parse_camera,
        metavar="CAMERA_ID:ANGLE_DEGREES:PATH",
        help="length-prefixed frame stream; specify exactly three",
    )
    parser.add_argument(
        "--encoding",
        default="raw",
        help="descriptive encoding label only; bytes are never transcoded",
    )
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
