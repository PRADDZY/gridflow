# GridFlow

GridFlow is a Grand Prix egress-planning prototype rebuilt around an explicit
external-reference boundary. It uses the public Iowa Department of
Transportation camera `DQTV17` to demonstrate real-time, vehicle-only video
analytics without claiming that data represents a race venue or using it to
direct venue operations.

```text
Iowa DOT public camera metadata
        |
Local HLS frame capture -> local RT-DETR vehicle detection
        |
Signed external-reference observation
        |
Cloudflare FastAPI Worker -> ReferenceState Durable Object
        |
GridFlow dashboard: live video, vehicle aggregates, audit, real map
```

## Components

- `gateway`: Docker-ready HLS gateway. It validates the Iowa DOT source,
  captures one frame in memory every 10 seconds, runs `PekingU/rtdetr_r50vd`
  locally, and posts vehicle-class aggregates. See [gateway/README.md](gateway/README.md).
- `services/control-api`: FastAPI Python Worker. Reference observations use a
  dedicated signed ingress path and `ReferenceState` Durable Object; they are
  structurally separate from the retained future venue-control pipeline.
- `apps/control-room`: Next.js interface showing the live HLS source, external
  attribution, vehicle-only metrics, audit samples, and a real map with Monza
  planning context plus the actual Iowa camera location.

## Boundaries

- The source is always `external_reference`; it is not a venue camera.
- The gateway stores no HLS frames or video segments. RT-DETR runs locally and
  only vehicle aggregate data leaves the host.
- The reference route contains no people count, crowd density, capacity, risk,
  signage, stewarding, or controller-action fields.
- The dashboard has no approve, publish, assignment, notification, or fake
  incident controls. Legacy venue-control routes remain hidden and Cloudflare
  Access-protected for a future authorised integration.
- The public source is attributed to Iowa DOT under CC BY 4.0. The live source
  is revalidated by the opt-in integration test before deployment.

## Verify locally

```powershell
cd services/control-api
uv sync --all-groups
uv run python -m pytest

cd ..\..\gateway
uv sync --extra vision --all-groups
uv run python -m pytest
$env:GRIDFLOW_RUN_LIVE_TESTS = "true"
$env:GRIDFLOW_RUN_MODEL_TESTS = "true"
uv run python -m pytest tests/test_live_iowa_source.py

cd ..\apps\control-room
npm.cmd ci
npm.cmd run lint
npm.cmd run test
npm.cmd run build
```

## Deploy

1. Deploy `services/control-api` with the `v2` Durable Object migration and
   configure `INGESTION_HMAC_SECRET` plus a controller read token.
2. Configure the dashboard's `CONTROL_API_READ_TOKEN` and deploy the
   Cloudflare Worker with its service binding.
3. Run the gateway container with the same ingress secret and Control API URL.
4. Verify source metadata, HLS playback, a local model sample, a signed
   reference observation, and dashboard freshness before treating it as live.

The source brief remains at `8a6e32e7-ff3e-4827-ba14-89e12bfc52eb.pdf`.
