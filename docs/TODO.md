# TODO

## Before robot

- [ ] Exchange one full Daniel job fixture and one result fixture.
- [ ] Decide full-job SSE versus SSE job ID + HTTP job fetch.
- [ ] Add end-to-end job idempotency after Daniel defines replay semantics.
- [ ] Keep the full standard-library test suite passing.

## After Daniel contract

- [ ] Adapt only `protocol/daniel.py` and `transport/daniel_api.py`.
- [ ] Wire authenticated job receipt and result/progress POSTs.
- [ ] Confirm canonical pose frame/units and desired-state retrieval.
- [ ] Run Daniel → mock robot → Daniel once, then replay the same job safely.

## After BracketBot API

- [ ] Implement semantic `observe()` with stable object IDs.
- [ ] Implement terminal `execute()` behind `RobotAdapter`.
- [ ] Confirm world-to-robot transform, tolerances, timeouts, and recovery.
- [ ] Map only supported robot actions; reject everything else.
- [ ] Run one-object restore five times in a row.
