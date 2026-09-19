# gitirl-agent

> Edge bridge between Daniel's GitIRL cloud app and Ryan/Sarah's robot code.

```text
Daniel cloud -- HTTP commands/state + SSE events --> gitirl-agent
gitirl-agent -- high-level RobotAction over HTTP --> robot-side adapter
robot-side adapter -- BBOS / Ryan-Sarah code --> BracketBot
```

This repository validates cloud input, converts Daniel's object/state payloads to stable internal types, sends high-level actions across `RobotAdapter`, and normalizes observations/results. It may verify and retry near the robot when that is useful.

**Do not move logic here unless it benefits from being close to the robot or cleanly isolates cloud and robot interfaces.**

## Ownership

This repo owns:

- Daniel JSON → `WorldState` / `RobotAction` translation.
- The robot-neutral `RobotAdapter` boundary.
- Conservative diff, restore, verification, and at-most-two retries.
- HTTP/SSE adapters, JSONL/CLI development tools, mocks, and tests.

It does **not** own AWS, Supabase, Elastic, SMS, frontend, authentication, cloud persistence, cloud NLP, low-level motor control, BracketBot daemons, perception, manipulation, or VLA behavior.

Only `moved` discrepancies become `MOVE_OBJECT`. Added, missing, relational, malformed, or unsupported work is reported instead of guessed.

## Transport choice

- **HTTP JSON** for commands, state snapshots, robot actions, and terminal results.
- **SSE** for low-rate Daniel→edge notifications and progress events.
- **HTTP POST** for optional camera frames; this is deferred.
- **No WebSockets.** Continuous bidirectional transport is unnecessary for the current job model.

Daniel-specific shapes live in [`protocol/daniel.py`](src/gitirl_agent/protocol/daniel.py) and [`transport/daniel_api.py`](src/gitirl_agent/transport/daniel_api.py). Robot-specific code stays behind [`robot/interface.py`](src/gitirl_agent/robot/interface.py).

## Current robot boundary

```python
observe() -> WorldState
execute(action: RobotAction) -> ActionResult
```

The robot-side HTTP template exposes `GET /v1/observation` and `POST /v1/actions`. Ryan/Sarah supply the backend; this repo does not call joints, torque, drive, or Sarah's `precision_placement.py` directly.

Sarah's current script saves/replays named joint poses locally and opens safety-sensitive BBOS writers during `goto`. It is ongoing robot work, not yet an object-placement API.

## Run

Interactive mock:

```bash
python3 scripts/run_dev.py
```

JSONL:

```bash
python3 scripts/run_dev.py --jsonl
```

Mock robot HTTP API:

```bash
python3 scripts/run_robot_api.py --mock
```

Listen to Daniel's SSE feed:

```bash
GITIRL_CLOUD_BASE_URL=http://127.0.0.1:8000 python3 scripts/listen_cloud.py
```

Tests:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

There are no required third-party runtime dependencies. See [`docs/INTEGRATION.md`](docs/INTEGRATION.md) before connecting real services.
