# Tonight's integration checklist

## Need from Daniel

- [ ] Final command WebSocket or HTTP endpoint.
- [ ] Authentication requirements and how secrets are supplied.
- [ ] Authoritative inbound JSON schema.
- [ ] Authoritative outbound JSON schema.
- [ ] Whether Daniel sends raw text, normalized `GitIRLCommand`, or both.
- [ ] `request_id` creation, uniqueness, correlation, and lifetime.
- [ ] Duplicate delivery and idempotency behavior.
- [ ] Acknowledgement semantics.
- [ ] Progress/status events and terminal-result semantics.
- [ ] Timeout, reconnect, heartbeat, and backoff behavior.
- [ ] Error envelope and error codes.
- [ ] Local development endpoint or captured message fixtures.
- [ ] Whether desired-state retrieval happens through the cloud or is included in a command.
- [ ] Whether robot communication is direct or routed through Daniel's backend.
- [ ] Deployment/runtime expectations for this process.
- [ ] Camera/media endpoint, codec, framing, limits, and backpressure only if this repo remains in that path.

When Daniel's contract arrives, start in:

- `src/gitirl_agent/protocol/messages.py`
- `src/gitirl_agent/protocol/serialization.py`
- `src/gitirl_agent/transport/websocket_client.py`
- `scripts/run_dev.py` only for composition/wiring

Do not put backend-specific fields into planner, state, verification, or robot modules.

## Need from Ryan and Sarah

- [ ] Actual BracketBot observation API and one captured example.
- [ ] Actual action/execution interface and one minimal example.
- [ ] Stable object identity behavior across observations.
- [ ] Position and orientation representation.
- [ ] Relationship, confidence, and metadata semantics.
- [ ] Supported high-level actions and required arguments.
- [ ] Completion, retryable failure, hard failure, cancellation, and timeout semantics.
- [ ] Whether execution is synchronous or asynchronous.
- [ ] Re-observation availability and freshness after an action.
- [ ] Typical perception and action latency.
- [ ] Reset/recovery procedure after a failed action.
- [ ] Physical tolerances for deciding whether an object is restored.
- [ ] Camera capture interface and formats only if media crosses this repo.

Robot integration should start in:

- `src/gitirl_agent/robot/interface.py`
- a new concrete adapter beside `robot/mock.py`
- `src/gitirl_agent/state/models.py` only if confirmed observation data requires a generic-model adjustment
- `src/gitirl_agent/planner/models.py` only if a confirmed high-level action requires it

Do not expose BracketBot calls outside the concrete adapter.

## First integration test: cloud with mock robot

```text
Daniel sends: restore study
→ protocol layer converts it to GitIRLCommand
→ validation succeeds
→ MockRobotAdapter executes the existing restore flow
→ structured result preserves request_id
→ result returns to Daniel
```

Pass condition: one request completes end to end without backend fields leaking into core modules.

## Second integration test: real robot adapter

```text
replace MockRobotAdapter with real adapter
→ observe one supported object
→ produce one MOVE_OBJECT action
→ execute one action
→ receive normalized ActionResult
→ re-observe
→ verify once
```

Pass condition: one object restores successfully with no speculative action or infinite retry.

## Routing decision

Do not decide direct-versus-backend-routed robot communication in code before the team answers it. Direct integration can keep the current synchronous adapter. Backend-routed integration needs an asynchronous request/result implementation keyed by `request_id`, but the internal command, state, diff, action, and result types can remain.
