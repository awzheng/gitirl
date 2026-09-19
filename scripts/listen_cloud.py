#!/usr/bin/env python3
"""Print Daniel's SSE events as JSONL; never executes robot actions."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.gitirl_agent.transport.daniel_api import DanielAPIClient, DanielAPIError
from src.gitirl_agent.protocol.daniel import robot_actions_from_daniel_job
from src.gitirl_agent.robot.http_contract import robot_action_to_dict


def event_document(event):
    """Make job events inspectable without ever executing them."""

    document = {"event": event.event, "id": event.event_id, "data": event.data}
    if event.event != "job" or not isinstance(event.data, dict):
        return document
    if not isinstance(event.data.get("ops"), list):
        document["actionable"] = False
        document["reason"] = "job event does not include executable ops"
        return document
    try:
        translated = robot_actions_from_daniel_job(event.data)
    except ValueError as error:
        document["actionable"] = False
        document["reason"] = str(error)
        return document
    document["actionable"] = bool(translated.actions) and not translated.unsupported
    document["actions"] = [robot_action_to_dict(action) for action in translated.actions]
    document["unsupported"] = [
        {
            "object_id": item.object_id,
            "operation": item.operation,
            "reason": item.reason,
        }
        for item in translated.unsupported
    ]
    return document


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="exit after the first event")
    args = parser.parse_args()
    client = DanielAPIClient.from_environment()
    if client is None:
        raise SystemExit("GITIRL_CLOUD_BASE_URL must be set")

    last_event_id = None
    backoff_seconds = 1.0
    while True:
        try:
            for event in client.events(last_event_id):
                if event.event_id:
                    last_event_id = event.event_id
                print(json.dumps(event_document(event), separators=(",", ":")), flush=True)
                backoff_seconds = 1.0
                if args.once:
                    return
        except (DanielAPIError, OSError) as error:
            print(f"cloud SSE disconnected: {error}; retrying", file=sys.stderr)
        time.sleep(backoff_seconds)
        backoff_seconds = min(backoff_seconds * 2, 15.0)


if __name__ == "__main__":
    main()
