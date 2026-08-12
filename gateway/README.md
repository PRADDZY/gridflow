# GridFlow Reference Gateway

This gateway samples the public Iowa Department of Transportation camera
`DQTV17` and runs `PekingU/rtdetr_r50vd` locally. It sends only vehicle-class
counts, confidence, inference latency, and a one-minute flow delta to the
GridFlow Control API. The source is always marked `external_reference`; it is
not a venue camera and cannot trigger signage, stewarding, or capacity actions.

The gateway queries Iowa DOT's public traffic-camera feature service for the
current HLS URL. It allows only `*.iowadot.gov` video hosts, verifies the
returned camera identifier, captures one HLS frame in memory, and never writes
frames or playlist segments to disk. The model is downloaded once into the
local Hugging Face cache and inference happens in the gateway process.

## Required configuration

```text
CONTROL_API_URL=https://your-control-api.workers.dev
INGESTION_HMAC_SECRET=<same secret configured on the Control API>
```

Optional settings:

```text
REFERENCE_SOURCE_ID=iowa-dq-dqtv17
IOWA_CAMERA_ID=DQTV17
DETECTOR_MODEL=PekingU/rtdetr_r50vd
DETECTOR_REVISION=main
DETECTOR_THRESHOLD=0.5
POLL_INTERVAL_SECONDS=10
```

No Hugging Face access token, remote inference endpoint, RTSP credential, or
synthetic-data setting is used by this runtime path.

## Run and test

```powershell
uv sync --extra vision --all-groups
uv run python -m pytest

$env:GRIDFLOW_RUN_LIVE_TESTS = "true"
$env:GRIDFLOW_RUN_MODEL_TESTS = "true"
uv run python -m pytest tests/test_live_iowa_source.py

uv run gridflow-gateway monitor-reference --once
uv run gridflow-gateway monitor-reference
```

The default test suite uses deterministic metadata and detection fixtures.
The opt-in test verifies the live Iowa DOT metadata feed, its HLS playlist, and
local RT-DETR execution on one current public frame.

## Container deployment

The included `Dockerfile` installs the `vision` extra. `docker-compose.yml`
keeps the model cache in a named volume and samples every 10 seconds:

```powershell
$env:CONTROL_API_URL = "https://your-control-api.workers.dev"
$env:INGESTION_HMAC_SECRET = "replace-with-the-shared-ingress-secret"
docker compose up --build -d
```

For any operational venue deployment, use an authorised camera source and a
separate, reviewed control path. This reference gateway intentionally has no
venue-control input or output.

## Direct Linux service deployment

For a small ARM host where a Docker image is impractical, install the project
with `uv sync --extra vision --all-groups`, place the required configuration in
`/var/oled/gridflow-reference/.env` with mode `0600`, and install the supplied
service unit:

```sh
sudo install -o root -g root -m 644 deploy/gridflow-reference-gateway.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now gridflow-reference-gateway
sudo systemctl status gridflow-reference-gateway
```

The service persists only the model cache. It does not persist source frames,
video segments, or observations.
