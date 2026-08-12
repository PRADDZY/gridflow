# GridFlow Venue Gateway

This process runs at the venue boundary, where it can access an approved RTSP
camera source. It sends one JPEG frame to authenticated Hugging Face inference
endpoints, validates both responses, and signs the derived observation for the
GridFlow Control API. It never sends camera credentials to Cloudflare.

## Required configuration

```text
CONTROL_API_URL=https://your-control-api.workers.dev
INGESTION_HMAC_SECRET=<same secret configured on the Control API>
HF_TOKEN=hf_...
HF_DETECTOR_ENDPOINT=https://<dedicated-detector-endpoint>
HF_DENSITY_ENDPOINT=https://<dedicated-density-endpoint>
```

`HF_DETECTOR_ENDPOINT` uses Hugging Face's object-detection response shape.
The detection model defaults to `PekingU/rtdetr_r50vd`. The density endpoint
must return this narrow JSON contract:

```json
{"people_count": 436, "confidence": 0.88}
```

The gateway rejects malformed inference responses and does not post a partial
observation. The Control API separately downgrades stale, low-confidence, or
disagreeing estimates to controller review.

## Run

```powershell
uv sync --extra rtsp
uv run python -m unittest discover -s tests -v
uv run gridflow-gateway submit-rtsp `
  --source "rtsp://camera.example/stream" `
  --event-id monza-2026 `
  --camera-id cam-04 `
  --zone-id south-exit `
  --capacity 520 `
  --queue-change-per-minute 18
```

Use a dedicated authenticated Hugging Face Inference Endpoint for production,
with the model revision recorded in `HF_DETECTOR_REVISION` and
`HF_DENSITY_REVISION`.
