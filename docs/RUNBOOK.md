# Development runbook

## Local CLI mode

```bash
python3 scripts/run_dev.py
```

No dependency installation is required. The local development fixture contains a saved `study` state and a moved `box_A`.

The most predictable MVP commands are:

```text
gitirl diff study
gitirl restore study
gitirl commit demo
```

They use deterministic parsing and require no LLM or network service.

## JSON-lines mode

For local process-to-process integration:

```bash
python3 scripts/run_dev.py --jsonl
```

Example input line:

```json
{"type":"user_command","request_id":"demo-1","payload":{"text":"gitirl diff study"}}
```

The process writes only protocol JSON lines to stdout. This is suitable for shell pipes and teammate-owned development adapters; it is not a finalized robot transport.

## Local JSON state persistence

Set an explicit path to persist development commits:

```bash
export GITIRL_STATE_FILE='.gitirl/states.json'
python3 scripts/run_dev.py
```

The file uses a small versioned JSON wrapper. It is intentionally behind `StateStore` so Daniel's persistence adapter can replace it later.

## WebSocket mode

Install the optional transport dependency yourself:

```bash
python3 -m pip install -r requirements.txt
```

Then export the values Daniel provides:

```bash
export GITIRL_WS_URL='...'
export GITIRL_WS_TOKEN='...'
python3 scripts/run_dev.py
```

There is no default endpoint. If `GITIRL_WS_URL` is absent or empty, the script uses local CLI mode.

## Troubleshooting

- `WebSocket mode requires...`: install `requirements.txt` into a virtual environment.
- Connection failures: confirm the URL, token behavior, local endpoint, and reconnect expectations with Daniel.
- `UNKNOWN_STATE`: the current in-memory store has no state with that name.
- `UNSUPPORTED_COMMAND`: parsing succeeded, but that command is not orchestrated yet.
- `CONFLICT`: the planner or verifier could not produce or confirm a safe generic move.

## Safety

The development script always uses `MockRobotAdapter`. Do not substitute a real adapter until Ryan and Sarah confirm the official interface and physical safety constraints.
