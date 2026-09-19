# Cloud contract — what to do before you send a command to the robot

From the gitspace cloud side (Daniel). Everything below was verified against the running
server, and against **your** code at `9582081` — your `protocol/daniel.py` was run on our live
`/api/state` and `/api/command` responses, not on fixtures.

Your `PROTOCOL.md` says our schema is authoritative once finalized. This is that.

---

## 0. What already works — don't rebuild it

Your `tests/test_daniel_contract.py` passes against our live data:

- `world_state_from_daniel(GET /api/state?ref=HEAD)` → **11 objects parsed**, and
  `metadata["coordinate_frame"] == "canonical_world_z_up"`.
- `robot_actions_from_daniel_job(POST /api/command …)` → a `RobotAction(MOVE_OBJECT …)`
  carrying our `job_id` as its `request_id`.

So the state and job shapes are settled. The rest of this is what you still have to decide.

---

## 1. The frame, stated once, so nothing is inferred

Every response carrying poses has explicit `frame` and `units` fields. Read them; never guess.

- **Frame:** `canonical_world_z_up` — **Z is up**.
- **Units:** metres, and **degrees** for `yaw` (`delta_m`, `delta_yaw_deg`).

**Bracket Bot's native frame is Y-down.** That conversion belongs at *your* adapter boundary
(`robot/http_adapter.py`), applied exactly once. Two conversions, or none, produces an arm that
is 90° off and reads as an IK bug rather than a frame bug — it will cost you hours.

---

## 2. A job is named by what it would DO

```
job_id = "job_" + sha256("gitspace.job/1", command, target sha, HEAD sha, room digest)[:16]
```

The same command against the same room is the **same job**. Verified: the identical revert twice
returns `job_433ea50059117524` both times.

- Asking twice returns the stored job with `replayed: true`, whatever state it is in.
- A job **runs once**. The first report claims it for that report's `run_id`; reports from any
  other run are refused (`claimed`).
- The first terminal report (`success` | `failed`) stands. An identical body again →
  `replayed: true`. A different one → `result_conflict`.

**So a retry after a dropped connection can never become a second physical run.** You do not need
your own dedupe. A genuinely new attempt requires a new room — the rescan after a run moves HEAD,
which names a new job.

---

## 3. Reporting back is authenticated; reading is not

```
GET  /api/jobs/{job_id}          no token
POST /api/jobs/{job_id}/result   Authorization: Bearer $GITIRL_CLOUD_TOKEN
```

A result is the robot claiming a *physical action happened*, and `:8000` is publicly reachable,
so the write is authenticated from everyone, loopback included. Your `DanielAPIClient` already
sends this header. With no token configured the write fails **closed** (503) — never open.

`GET /api/state` and `GET /api/jobs/{id}` carry the same poses we already serve publicly, so they
take no token.

---

## 4. ⚠️ The thing to settle before you drive the robot

**Your layer only executes `moved`.** Running your translator on our real revert of `1a668ec`:

| op | your verdict |
|---|---|
| `moved` (mug) | `RobotAction(MOVE_OBJECT …)` |
| `removed` (scissors) | `UnsupportedCloudOperation` |
| `added` | `UnsupportedCloudOperation` |

Your stated reason — *"only moved operations have a confirmed robot-independent action"* — is
correct, and we are not asking you to guess. But it means **two of the three ops in our headline
revert cannot be executed**, so the demo either reverts a `moved`-only commit or we agree what
these mean physically:

- **`removed`** — the object is in the target state but not in the room. The robot cannot
  materialise it. Options: skip with a reason surfaced in the UI, or treat it as
  "fetch from a known staging zone", which needs a staging zone in the contract.
- **`added`** — the object is in the room but not in the target state. Physically this is
  "put it away", which needs a destination. Same answer needed: a staging zone, or skip.

**Decide these two, or scope the demo to `moved`.** Everything else is ready. This is the one
open item that changes whether the robot actually moves during judging.

---

## 5. Before you send anything to the robot — preflight

1. **`GET /api/jobs/{job_id}`** and read `motion`. It is `"mock_only"` until the operator sets
   `JOBS_REAL_MOTION=1`. Do not drive hardware while it says `mock_only`.
2. **Check `frame` and `units`** on the payload and convert Z-up → robot-native **once**, in
   your adapter.
3. **Split the ops**: execute `moved`; surface `unsupported` explicitly rather than dropping it
   silently — an op that vanishes looks like a robot failure during a demo.
4. **Execute in the given order.** `ops` is an ordered plan, not a set.
5. **Report once**, terminal, with your `run_id`. Do not retry a terminal report with a
   different body; it will be refused as `result_conflict`.
6. **Never write `room.git`.** A report is a *claim*, recorded. Our rescan decides what the room
   IS. That separation is what makes the git history trustworthy.

---

## 6. Where the text comes from

The panel posts your envelope unchanged:

```json
{"type":"user_command","request_id":"…","payload":{"text":"set my room back to study mode"}}
```

Your parser deciphers it; ours is only a labelled fallback when yours is not reachable, and every
response says which served it (`served_by`). Your grammar is deterministic regex over six verbs
(`add, commit, status, diff, restore, log`), so anything conversational returns
`unknown_command` — that is expected, not a bug, and the UI shows it as "not understood" rather
than failing.

Note we say `revert` where you say `restore`. They are **not** aliases and we have deliberately
not mapped one onto the other; if you need `revert` semantics, ask and we will add the verb.

---

## 7. You do NOT need Elastic or OpenAI keys — you already have both, as endpoints

Your `docs/ARCHITECTURE.md` already draws this line: *"Daniel owns UI, Elastic search, object
history, cloud data, authentication, and any NLP."* This section is just the how.

The cloud holds the Elastic and OpenAI credentials and does the work. You call an endpoint with
the token you already have. **Do not ask for the raw keys, and do not put them in this repo —
it is public, and a key committed here is scraped within minutes.**

### Semantic search over the room — `GET /api/search`

```
GET /api/search?q=<text>&limit=20&all_time=true      no token
```

This is hybrid retrieval (BM25 + dense vectors + reranking), not a keyword filter. Verified live:

```
GET /api/search?q=something%20to%20write%20with
  → marker_c3d4    1.1346
    notebook_5a0c  1.0355
    bowl_0c55      1.0276
```

The query contains none of those words. BM25 alone cannot get from *"something to write with"* to
a marker — that hit comes from the vector side. Use this instead of matching on `class` strings.

The response carries `retriever`, `reranked`, `bm25_fields`, `took_ms` and `provenance`, so you
can see **how** a hit was produced rather than trusting a bare score. `q` is 1–200 chars,
`limit` 1–50, and `all_time=false` scopes to a `head`.

### The LLM leg — `POST /api/seer/ask`

```
POST /api/seer/ask   {"capture_id": "cap_0912"}
GET  /api/seer/status
```

It takes a **`capture_id`, not a free-text question**: it finds that capture's Sentry issue,
starts Seer on it and polls. A `stumped` result is an **answer** at HTTP 200 — never an error and
never fabricated.

### Why this is the right shape, not us being precious

- One credential to revoke. If `GITIRL_CLOUD_TOKEN` leaks, we rotate one value. If an Elastic or
  OpenAI key leaks, that is credential rotation plus a spend audit.
- Every call runs through the cloud, so it lands in our Sentry traces and Elastic logs. With raw
  keys your usage would be invisible to us and undebuggable together.
- Data rules stay enforced in one place: Elasticsearch first, a fixture only when ES is genuinely
  unavailable and always labelled `source`, and a value that was not recorded is `null` — never a
  made-up number. That guarantee cannot hold if callers query the cluster directly.

**If you need a capability these two do not cover, ask for the endpoint, not the key.** Adding an
endpoint takes minutes and keeps your edge dependency-free — which is worth protecting, since your
`requirements.txt` currently reads *"No runtime dependencies."*
