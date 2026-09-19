# Development runbook

## Local edge

```bash
python3 scripts/run_dev.py
python3 scripts/run_dev.py --jsonl
```

The CLI and JSONL modes use deterministic parsing and need no network or LLM. Optional local state:

```bash
GITIRL_STATE_FILE=.gitirl/states.json python3 scripts/run_dev.py
```

## Mock robot over HTTP

Terminal 1:

```bash
python3 scripts/run_robot_api.py --mock
```

Terminal 2:

```bash
GITIRL_ROBOT_BASE_URL=http://127.0.0.1:8765 python3 scripts/run_dev.py
```

## Daniel SSE smoke test

```bash
GITIRL_CLOUD_BASE_URL=http://127.0.0.1:8000 python3 scripts/listen_cloud.py
```

This listens and prints events only. Daniel's current `job` SSE payload lacks executable `ops`, and the current event inlet is loopback-only, so no real action/result loop is claimed yet.

## Tests

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

## Troubleshooting

- `UNKNOWN_STATE`: the local store has no matching state.
- `CONFLICT`: the edge refused to guess an unsupported physical action.
- Cloud disconnect: check `GITIRL_CLOUD_BASE_URL`; the listener reconnects with bounded backoff.
- Robot connection error: check `GITIRL_ROBOT_BASE_URL`, token, and `/health`.
- Never start a real robot backend until Ryan/Sarah confirm writer ownership and safety.
