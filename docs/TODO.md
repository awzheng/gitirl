# TODO

## Before robot

- [ ] Keep all 17 baseline tests passing.
- [ ] Exchange one inbound and one outbound JSON fixture with Daniel.
- [ ] Agree on direct versus backend-routed robot communication.
- [ ] Prepare one `WorldState` fixture and one `MOVE_OBJECT` fixture for Ryan/Sarah.
- [ ] Keep camera streaming deferred unless the team explicitly places it in this service.

## After Daniel contract

- [ ] Adapt `protocol/messages.py` and `protocol/serialization.py` to the authoritative schemas.
- [ ] Configure endpoint, authentication, acknowledgement, heartbeat, reconnect, and error behavior in `transport/`.
- [ ] Preserve `request_id` end to end and implement only the agreed idempotency behavior.
- [ ] Replace or bypass local state persistence according to cloud ownership.
- [ ] If robot traffic routes through Daniel, adapt orchestration to asynchronous request/result correlation.

## After BracketBot API

- [ ] Implement a concrete `RobotAdapter` with Ryan/Sarah.
- [ ] Translate real observations into `WorldState`.
- [ ] Translate supported `RobotAction` values into confirmed robot calls.
- [ ] Normalize completion/failure into `ActionResult`.
- [ ] Set verification tolerances and timing from measured hardware behavior.
- [ ] Run one-object restore, failure recovery, and five consecutive demo trials.
