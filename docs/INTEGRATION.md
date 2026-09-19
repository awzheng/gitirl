# Caretaker integration

## Daniel → edge

Daniel's current useful endpoints are:

- `GET /api/search?q=...`
- `GET /api/object-life/{object_id}`
- `POST /api/object-life/{object_id}/point`

The point endpoint already returns `job_id`, `object_id`, `target_pose`, and `zone`. Daniel should forward that complete response to:

```http
POST http://ANDREW_IP:8780/v1/jobs
Authorization: Bearer <HOUSEBOT_EDGE_TOKEN>
```

Do not use Daniel's SSE job summary for execution: it omits the target pose/operations.

Still needed from Daniel:

- one real point-job fixture;
- one result callback endpoint, or acceptance of the synchronous edge response;
- stable `job_id` semantics;
- confirmation that object poses are canonical world Z-up/metres/yaw-degrees;
- an agreed confidence/ambiguity gate.

## Edge → robot

The edge calls:

- `GET /health`
- `GET /v1/observation?request_id=...`
- `POST /v1/actions`

Still needed from Ryan/Sarah:

- a real `RobotAPIBackend` implementation;
- support for one finite `POINT_AT_OBJECT` or `MOVE_OBJECT` action;
- world-to-robot coordinate conversion;
- terminal success/retryable/failure semantics;
- writer-busy detection, timeout, cancellation, and torque release;
- a fresh observation if physical verification is used.

Sarah's current named joint-pose CLI is not yet this service contract and must not be invoked concurrently with another BBOS writer.

## First demo path

```text
“Where are my keys?”
→ Daniel /api/search
→ keys_7c2e
→ Daniel /point job
→ POST complete job to Housebot Edge
→ POINT_AT_OBJECT
→ robot points
→ terminal result returned
```

Do this five times before adding manipulation, Git history, or NLP polish.
