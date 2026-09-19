# gitirl-agent

> Thin edge/integration bridge between GitIRL's cloud backend and robot-side software.

```text
Daniel's cloud/backend
        ↓ high-level command
gitirl-agent edge bridge
        ↓ RobotAction through RobotAdapter
Ryan/Sarah's robot stack
        ↑ observation / action result
gitirl-agent verification + normalization
        ↑ structured result
Daniel's cloud/backend
```

`gitirl-agent` receives high-level commands, validates and normalizes them into stable internal types, crosses the `RobotAdapter` boundary, optionally performs verification/retry close to the robot, and normalizes results for the cloud. It also provides mocks and local tools for integration testing.

> **Do not move logic into gitirl-agent unless it benefits from being close to the robot or cleanly isolates cloud and robot interfaces.**

## Ownership

This repository owns:

- Stable `GitIRLCommand`, `WorldState`, `StateDiff`, `RobotAction`, and result types.
- Validation and conservative diff-to-action translation.
- `RobotAdapter` as the robot boundary.
- Local restore, diff, commit, verification, and maximum-two-retry behavior.
- Provisional protocol/transport adapters, mocks, JSONL mode, and tests.

This repository does **not** own:

- AWS, Supabase, Elastic, SMS, frontend, authentication, cloud persistence, or general cloud orchestration.
- General-purpose agents, LLM infrastructure, or cloud-side NLP.
- BracketBot internals, perception implementation, manipulation logic, joints, trajectories, or low-level motor control.
- Production camera capture, panorama stitching, or media infrastructure.

Daniel owns the first category. Ryan and Sarah own the robot-specific category. Natural-language parsing here is a replaceable development fallback; the reliable input is a structured command such as `{"command":"restore","target_state":"study"}`.

## Current core

```text
command
→ validate
→ load desired state / observe current state
→ deterministic diff
→ small deterministic plan
→ RobotAdapter
→ re-observe
→ verify
→ retry at most twice or return result
```

Only `MOVED` currently produces `MOVE_OBJECT`. Missing, added, relational, and unknown differences become conflicts instead of guessed behavior.

## Integration boundaries

- Daniel-specific message schemas belong in `src/gitirl_agent/protocol/` and connection behavior in `src/gitirl_agent/transport/`.
- Robot-specific translation belongs behind [robot/interface.py](src/gitirl_agent/robot/interface.py).
- Planner, state, and verification code must not learn Daniel's wire schema or BracketBot APIs.
- The current `RobotAdapter` is synchronous and safe for mock/direct integration. If robot calls route asynchronously through Daniel, adapt or replace the adapter/orchestration call site after that contract is known.

See [ARCHITECTURE.md](docs/ARCHITECTURE.md), [INTEGRATION.md](docs/INTEGRATION.md), and [PROTOCOL.md](docs/PROTOCOL.md) before changing integration code.

## Run

Interactive:

```bash
python3 scripts/run_dev.py
```

JSONL process integration:

```bash
python3 scripts/run_dev.py --jsonl
```

Tests:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Optional WebSocket dependency:

```bash
python3 -m pip install -r requirements.txt
```

Optional local state file:

```bash
GITIRL_STATE_FILE=.gitirl/states.json python3 scripts/run_dev.py
```

The WebSocket and camera protocols are provisional until Daniel provides authoritative contracts. The camera scaffold is deferred unless the team confirms that media should pass through this process.
