# GridFlow Control API

This Cloudflare Python Worker accepts signed queue observations and returns a
recommendation for a human controller. It is intentionally not an automation
endpoint: every output has `requires_human_approval: true`.

Accepted recommendations are stored with their current controller decision in
the event's Durable Object. Controller clients can read
`GET /v1/events/{event_id}/current` only with the
`x-gridflow-controller-token` header. It returns an `EventSnapshot` containing
the recommendation and, if one exists, the decision.

## Safety policy encoded here

- An observation with a camera age above 25 seconds is `review`, not `critical`.
- Low model confidence or detector/density disagreement is `review`.
- A valid observation is `critical` only when estimated occupancy is at least
  80% and queue growth is at least 10 people per minute.
- `sign_action` and `steward_action` are recommendations. A controller must
  approve and publish them through the operational workflow.
- A new observation replaces the active snapshot and clears its earlier
  decision. `POST /v1/events/{event_id}/decisions` rejects decisions that name
  an older recommendation with `409 Conflict`.

## Signed ingress contract

`POST /v1/observations` requires these headers:

```text
x-gridflow-sent-at: Unix seconds
x-gridflow-signature: sha256=<HMAC_SHA256("<sent_at>.<raw JSON body>")>
```

The Worker reads `INGESTION_HMAC_SECRET` from its Cloudflare environment
bindings and rejects unsigned, bad, or older-than-60-second requests.
Configure distinct `CONTROLLER_READ_TOKEN` and `CONTROLLER_ACTION_TOKEN`
secrets. Decisions require the action token, a `recommendation_id`, and a
controller identity supplied by the Access-protected dashboard; the Worker
records that identity with the decision. The last 100 decisions per event are
available to authorized controllers at `GET /v1/events/{event_id}/audit`.

## Local development

```powershell
uv sync --all-groups
uv run python -m unittest discover -s tests
$env:INGESTION_HMAC_SECRET = "replace-with-a-local-secret"
uv run uvicorn --app-dir src api:app --port 8787
```

Set `INGESTION_HMAC_SECRET` before manually posting to the ingestion endpoint.
The API reads a Cloudflare binding in the Worker and uses the process
environment only for native local development.

`pywrangler` bundles this Worker for Cloudflare. That package step is checked
by the Ubuntu GitHub Action in this repository because current native Windows
uv/Pyodide tooling cannot install the wasm virtual environment. Run
`uv run pywrangler deploy` from Linux or the Ubuntu deployment workflow.

Cloudflare's Python Workers are currently beta and require the
`python_workers` compatibility flag in `wrangler.toml`.
