# scripts/

Small development/integration utilities. Core logic stays in `src/`.

| File | Purpose | Inputs | Outputs | Env vars |
| --- | --- | --- | --- | --- |
| `run_dev.py` | Mock CLI or JSONL edge flow | text / JSONL | JSON envelopes | `GITIRL_STATE_FILE`, `GITIRL_ROBOT_*` |
| `listen_cloud.py` | Read Daniel SSE events; no robot execution | `/api/events` | JSONL events | `GITIRL_CLOUD_BASE_URL`, `GITIRL_CLOUD_TOKEN` |
| `run_robot_api.py` | Mock robot HTTP API | HTTP | observation/result JSON | `GITIRL_ROBOT_TOKEN` |
| `inspect_bracketbot.py` | Read-only BBOS smoke test | BBOS topics | JSON summary | `PYTHONPATH` |
| `stream_cameras.py` | Deferred HTTP frame sender | BBOS or framed files | HTTP POST bodies | `GITIRL_CAMERA_HTTP_*` |

Rules:

- No core logic, credentials, cloud infrastructure, or invented robot behavior.
- Scripts call `src/`; do not duplicate contracts.
- Update this table when scripts change.

Read `README.md`, `docs/ARCHITECTURE.md`, `docs/INTEGRATION.md`, and `docs/PROTOCOL.md` before changing integration code.
