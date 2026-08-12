# GridFlow

GridFlow is a race-day queue-safety control room for Grand Prix venues. It
turns approved CCTV observations into confidence-aware recommendations for an
event controller, steward coordination, and digital signage. It is decision
support: models never instruct staff or publish signage on their own.

## What is implemented

```text
Approved RTSP camera
        |
Venue gateway -> Hugging Face detector + density endpoints
        |
Signed observation
        |
Cloudflare FastAPI Worker -> event Durable Object -> controller dashboard
                                                    -> approved signage payload
```

- `apps/control-room`: Next.js operator board and public display surface,
  deployed with OpenNext for Cloudflare.
- `services/control-api`: FastAPI Python Worker. It verifies HMAC-signed
  ingress, fails closed on stale or uncertain evidence, and stores the latest
  recommendation plus its controller decision per event in a Durable Object.
- `gateway`: venue-side RTSP capture, Hugging Face endpoint client, response
  validation, and signed Control API submission.

## Safety boundaries

- Camera frames stay at the venue gateway except for the configured, approved
  Hugging Face inference endpoints. Camera credentials never enter Cloudflare.
- A camera older than 25 seconds, low model confidence, or detector/density
  disagreement results in `review`, not an operational directive.
- Every recommendation declares `requires_human_approval: true`.
- Every new observation clears the prior controller decision. An approval only
  applies to the exact recommendation identifier it reviewed.
- The dashboard validates a Cloudflare Access JWT before it can read or publish
  a decision; the authenticated Access email becomes the decision's audit
  identity. The public display receives only an allow-listed approved message,
  never raw queue data.
- Dashboard read and action tokens are separate. Gateway ingress is protected
  by a distinct short-lived HMAC signature.

## Run locally

```powershell
cd apps/control-room
npm.cmd install
npm.cmd run dev
```

The operator board is at `http://localhost:3000`; the signage page is at
`http://localhost:3000/display`.

```powershell
cd services/control-api
uv sync --all-groups
uv run python -m unittest discover -s tests -v

cd ..\..\gateway
uv sync
uv run python -m unittest discover -s tests -v
```

## Production handoff

1. Deploy the Control API from Linux or use the manual GitHub Actions workflow
   after setting `CLOUDFLARE_API_TOKEN` as a repository secret.
2. Configure the deployed API with distinct `INGESTION_HMAC_SECRET`,
   `CONTROLLER_READ_TOKEN`, and `CONTROLLER_ACTION_TOKEN` secrets.
3. Create a Cloudflare Access application for the controller dashboard and
   configure the control room's `CONTROL_API_URL`, `CONTROL_API_READ_TOKEN`,
   `CONTROL_API_ACTION_TOKEN`, `CF_ACCESS_TEAM_DOMAIN`, `CF_ACCESS_AUD`, and
   `CF_ACCESS_ALLOWED_EMAILS` secrets. The Access audience must match the
   controller application, and the allow-list must contain only approved event
   controllers.
4. Create authenticated Hugging Face Inference Endpoints for the detector and
   density model, then configure the venue gateway environment documented in
   [gateway/README.md](gateway/README.md).
5. Complete camera placement, calibration, privacy review, controller runbook
   training, and a supervised dry run before live event use.

## Demo media

The current board includes a Pexels queue-video still solely for the visual
demo. Production use replaces it with an approved camera gateway. The source
brief is retained as `8a6e32e7-ff3e-4827-ba14-89e12bfc52eb.pdf`.
