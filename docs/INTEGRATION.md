# Integration tonight

## What is already confirmed

Daniel's current repo is available locally at `../hack-the-north` and currently exposes:

- `GET /api/events`: SSE (`status`, `job`, `capture`, `conflict`, `telemetry`).
- `POST /api/command`: validates/plans a command and returns a job containing `ops`.
- `GET /api/state?ref=...`: objects with canonical world poses.
- `POST /api/internal/event`: **loopback-only**, unsuitable for a remote edge process.

`protocol/daniel.py` understands the current state/job shapes. `transport/daniel_api.py` contains all HTTP/SSE calls.

BracketBot exposes local BBOS readers. Sarah's current `precision_placement.py` is not a service API; do not invoke it from middleware.

## Need from Daniel

- Base HTTP URL and authentication.
- Decide how an executable job reaches the edge:
  - include full `ops` in the SSE `job` event, or
  - include a job ID and add an authenticated `GET /api/jobs/{id}`.
- An authenticated, non-loopback endpoint for acknowledgements, progress, and terminal results.
- Authoritative job/result schemas and error codes.
- `request_id`/`job_id` ownership, idempotency, replay, and cancellation rules.
- Confirm that `/api/state` remains the desired-state source.
- Confirm pose frame/units: current code says canonical world Z-up, metres, yaw-axis degrees.
- SSE reconnect/replay expectations and which job states are executable.
- A local test endpoint and one real fixture.

Until those exist, `scripts/listen_cloud.py` can observe events but intentionally cannot move the robot.

## Need from Ryan/Sarah

- A callable/service boundary for one supported object move.
- Exact request shape accepted by their code.
- World-to-robot pose transform and frame/unit rules.
- Stable object identity between observations.
- Fresh semantic observation shape after an action.
- Terminal success, retryable failure, hard failure, timeout, and cancellation semantics.
- Whether execution blocks until terminal or returns a job ID.
- Safe single ownership of BBOS control/torque writers.
- Physical verification tolerances.
- Recovery/reset procedure and measured latency.

They need to implement `RobotAPIBackend.observe()` and `RobotAPIBackend.execute()` in their own robot-side adapter. The HTTP template is in `robot/http_server.py`; no BBOS writer behavior is assumed.

## First integration test: Daniel + mock

1. Daniel creates a job with one `moved` op.
2. Edge receives the full job by the agreed HTTP/SSE path.
3. `robot_actions_from_daniel_job()` produces one `MOVE_OBJECT`.
4. `HTTPRobotAdapter` sends it to `scripts/run_robot_api.py --mock`.
5. Edge returns a correlated terminal result to Daniel.

Pass: one `job_id` is preserved end to end and replaying it does not execute twice.

## Second integration test: real robot

1. Replace only the mock robot backend.
2. Observe one known object.
3. Transform one canonical world target into the robot's confirmed frame.
4. Execute one supported move and receive a terminal result.
5. Re-observe and verify within measured tolerance.

## Files to touch

Daniel contract changes:

- `src/gitirl_agent/protocol/daniel.py`
- `src/gitirl_agent/transport/daniel_api.py`
- composition in `scripts/` only

Robot contract changes:

- `src/gitirl_agent/robot/interface.py`
- `src/gitirl_agent/robot/http_contract.py`
- Ryan/Sarah's concrete backend behind `robot/http_server.py`

Do not spread either side's fields into `state/`, `planner/`, `verification/`, or orchestration.
