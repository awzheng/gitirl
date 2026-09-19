# scripts/

Purpose: small development and integration utilities for `gitirl-agent`.

| File | Purpose | Inputs | Outputs | Environment |
| --- | --- | --- | --- | --- |
| `run_dev.py` | Run mock edge flow via CLI, JSONL, or provisional WebSocket | CLI text, JSONL envelopes, or WebSocket messages | Parsed-command and command-result envelopes | `GITIRL_WS_URL`, `GITIRL_WS_TOKEN`, `GITIRL_STATE_FILE` |
| `stream_cameras.py` | Deferred three-camera transport experiment; no real capture | Three length-prefixed byte streams | Provisional binary WebSocket frames | `GITIRL_CAMERA_WS_URL`, `GITIRL_CAMERA_WS_TOKEN` |

Rules:

- No core application logic in scripts; call `src/gitirl_agent/`.
- Never include credentials.
- Never assume BracketBot APIs or behavior.
- Never duplicate Daniel's cloud infrastructure.
- Keep camera streaming deferred until ownership and contracts are confirmed.
- Update this file whenever scripts change.

Before changing integration code, read:

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/INTEGRATION.md`
- `docs/PROTOCOL.md`
