import asyncio
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import sys
from pathlib import Path
import unittest

import httpx
from pydantic import ValidationError
from typer.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gridflow_gateway.cli import app
from gridflow_gateway.control_api import ControlApiClient
from gridflow_gateway.detection import summarize_vehicle_detections
from gridflow_gateway.flow import RollingVehicleFlow
from gridflow_gateway.iowa_dot import IowaDotCameraSource, PublicSourceError
from gridflow_gateway.models import (
    ReferenceCamera,
    ReferenceGatewaySettings,
    ReferenceObservation,
    VehicleClassCounts,
)
from gridflow_gateway.pipeline import build_reference_observation
from gridflow_gateway.signing import compact_json, signed_headers


NOW = datetime(2026, 8, 12, 8, 0, tzinfo=timezone.utc)
SETTINGS = ReferenceGatewaySettings(
    control_api_url="https://control.example.com",
    ingestion_hmac_secret="not-a-real-production-secret",
)


def source_payload(video_url: str = "https://video3.iowadot.gov:8888/cedarrapids/dqtv17lb/playlist.m3u8") -> dict:
    return {
        "features": [
            {
                "attributes": {
                    "COMMON_ID": "DQTV17",
                    "device_id": "DQTV17",
                    "Desc_": "US 20 at MM 297.2 - JFK Rd - West",
                    "Route": "US 20",
                    "UpdateDate": "2026-08-12",
                    "UpdateTime": "08:00:00",
                    "ImageURL": "https://example.com/current.jpg",
                    "VideoURL": video_url,
                    "latitude": 42.492226,
                    "longitude": -90.714405,
                }
            }
        ]
    }


def reference_camera() -> ReferenceCamera:
    return ReferenceCamera(
        source_id="iowa-dq-dqtv17",
        source_mode="external_reference",
        provider="Iowa Department of Transportation",
        attribution="Iowa Department of Transportation, CC BY 4.0",
        camera_id="DQTV17",
        name="US 20 at MM 297.2 - JFK Rd - West",
        route="US 20",
        latitude=42.492226,
        longitude=-90.714405,
        video_url="https://video3.iowadot.gov:8888/cedarrapids/dqtv17lb/playlist.m3u8",
    )


def reference_observation() -> ReferenceObservation:
    return ReferenceObservation(
        source=reference_camera(),
        captured_at=NOW,
        detector_model="PekingU/rtdetr_r50vd",
        detector_revision="main",
        class_counts=VehicleClassCounts(car=14, truck=2, bus=1, motorcycle=0),
        confidence=0.88,
        inference_ms=342,
        flow_delta_60s=4,
    )


class GatewayTests(unittest.TestCase):
    def test_signed_headers_match_control_api_contract(self) -> None:
        body = compact_json({"source_id": "iowa-dq-dqtv17", "vehicle_count": 17})
        headers = signed_headers(body, SETTINGS.ingestion_hmac_secret, sent_at=1_723_450_000)
        expected = hmac.new(
            SETTINGS.ingestion_hmac_secret.encode(),
            b"1723450000." + body,
            hashlib.sha256,
        ).hexdigest()

        self.assertEqual(headers["x-gridflow-signature"], f"sha256={expected}")
        self.assertEqual(headers["x-gridflow-sent-at"], "1723450000")

    def test_local_detector_counts_only_supported_vehicle_classes_above_threshold(self) -> None:
        summary = summarize_vehicle_detections(
            [
                {"label": "car", "score": 0.8},
                {"label": "person", "score": 0.99},
                {"label": "truck", "score": 0.51},
                {"label": "bus", "score": 0.49},
            ],
            threshold=0.5,
        )

        self.assertEqual(summary.class_counts.car, 1)
        self.assertEqual(summary.class_counts.truck, 1)
        self.assertEqual(summary.class_counts.bus, 0)
        self.assertEqual(summary.class_counts.motorcycle, 0)
        self.assertEqual(summary.confidence, 0.655)

    def test_rolling_flow_uses_the_oldest_observation_in_the_last_minute(self) -> None:
        flow = RollingVehicleFlow(window=timedelta(seconds=60))

        self.assertEqual(flow.observe(total_vehicles=10, captured_at=NOW), 0)
        self.assertEqual(flow.observe(total_vehicles=14, captured_at=NOW + timedelta(seconds=30)), 4)
        self.assertEqual(flow.observe(total_vehicles=20, captured_at=NOW + timedelta(seconds=70)), 6)

    def test_pipeline_builds_a_vehicle_only_reference_observation(self) -> None:
        created = build_reference_observation(
            camera=reference_camera(),
            captured_at=NOW,
            class_counts=VehicleClassCounts(car=3, truck=1, bus=0, motorcycle=0),
            confidence=0.72,
            inference_ms=240,
            flow_delta_60s=2,
        )

        self.assertEqual(created.source.source_mode, "external_reference")
        self.assertEqual(created.class_counts.car, 3)
        self.assertFalse(hasattr(created, "capacity"))

    def test_source_adapter_reads_iowa_camera_metadata(self) -> None:
        async def fetch() -> ReferenceCamera:
            def handler(request: httpx.Request) -> httpx.Response:
                self.assertEqual(request.url.params["where"], "COMMON_ID = 'DQTV17'")
                self.assertIn("VideoURL", request.url.params["outFields"])
                return httpx.Response(200, json=source_payload())

            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                return await IowaDotCameraSource(client).fetch("iowa-dq-dqtv17", "DQTV17")

        camera = asyncio.run(fetch())

        self.assertEqual(camera.provider, "Iowa Department of Transportation")
        self.assertEqual(camera.source_mode, "external_reference")
        self.assertEqual(camera.video_url.host, "video3.iowadot.gov")

    def test_source_adapter_rejects_a_video_host_outside_iowa_dot(self) -> None:
        async def fetch() -> None:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(lambda request: httpx.Response(200, json=source_payload("https://evil.example/stream.m3u8")))
            ) as client:
                await IowaDotCameraSource(client).fetch("iowa-dq-dqtv17", "DQTV17")

        with self.assertRaises(PublicSourceError):
            asyncio.run(fetch())

    def test_source_adapter_rejects_metadata_for_a_different_camera(self) -> None:
        payload = source_payload()
        payload["features"][0]["attributes"]["COMMON_ID"] = "DQTV99"

        async def fetch() -> None:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
            ) as client:
                await IowaDotCameraSource(client).fetch("iowa-dq-dqtv17", "DQTV17")

        with self.assertRaises(PublicSourceError):
            asyncio.run(fetch())

    def test_reference_camera_cannot_use_a_venue_control_source_mode(self) -> None:
        payload = reference_camera().model_dump(mode="json")
        payload["source_mode"] = "venue_control"

        with self.assertRaises(ValidationError):
            ReferenceCamera.model_validate(payload)

    def test_reference_client_posts_to_the_reference_ingress_path(self) -> None:
        async def submit() -> dict:
            def handler(request: httpx.Request) -> httpx.Response:
                self.assertEqual(request.url.path, "/v1/reference-sources/iowa-dq-dqtv17/observations")
                self.assertTrue(request.headers["x-gridflow-signature"].startswith("sha256="))
                self.assertEqual(json.loads(request.content)["source"]["source_mode"], "external_reference")
                return httpx.Response(200, json=reference_observation().model_dump(mode="json"))

            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                return await ControlApiClient(SETTINGS, client).submit_reference(reference_observation())

        recorded = asyncio.run(submit())

        self.assertEqual(recorded["class_counts"]["car"], 14)

    def test_synthetic_cli_command_is_not_available(self) -> None:
        result = CliRunner().invoke(app, ["submit-synthetic"])

        self.assertEqual(result.exit_code, 2)
        self.assertIn("unexpected extra argument", result.output)
