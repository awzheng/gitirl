#!/usr/bin/env python3
"""POST three provisional camera byte streams to an HTTP endpoint."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.gitirl_agent.media.camera_stream import (
    BBOSJPEGFrameSource,
    CameraHTTPSender,
    LengthPrefixedFrameSource,
)
from src.gitirl_agent.robot.bracketbot import CAMERA_TOPICS


def parse_camera(value: str):
    try:
        camera_id, angle, raw_path = value.split(":", 2)
        parsed_angle = None if angle.lower() in {"unknown", "none"} else float(angle)
        return camera_id, parsed_angle, Path(raw_path)
    except (TypeError, ValueError) as error:
        raise argparse.ArgumentTypeError(
            "camera must use CAMERA_ID:ANGLE_DEGREES_OR_UNKNOWN:PATH"
        ) from error


async def run(arguments: argparse.Namespace) -> None:
    url = os.environ.get("GITIRL_CAMERA_HTTP_URL")
    if not url:
        raise SystemExit("GITIRL_CAMERA_HTTP_URL must be set")

    if arguments.bbos:
        if arguments.camera:
            raise SystemExit("--bbos cannot be combined with --camera")
        sources = {
            camera_id: BBOSJPEGFrameSource(camera_id, topic)
            for camera_id, topic in CAMERA_TOPICS.items()
        }
    else:
        camera_values = arguments.camera or [
            ("head", None, Path("/tmp/gitirl-camera-head.frames")),
            ("left", None, Path("/tmp/gitirl-camera-left.frames")),
            ("right", None, Path("/tmp/gitirl-camera-right.frames")),
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

    sender = CameraHTTPSender(
        url=url,
        token=os.environ.get("GITIRL_CAMERA_HTTP_TOKEN"),
    )
    await sender.stream(sources)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bbos",
        action="store_true",
        help="read confirmed head/left/right JPEG topics on BracketBot",
    )
    parser.add_argument(
        "--camera",
        action="append",
        type=parse_camera,
        metavar="CAMERA_ID:ANGLE_OR_UNKNOWN:PATH",
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
