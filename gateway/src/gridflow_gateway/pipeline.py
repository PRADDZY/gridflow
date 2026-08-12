import asyncio
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from gridflow_gateway.control_api import ControlApiClient
from gridflow_gateway.flow import RollingVehicleFlow
from gridflow_gateway.frame import capture_video_frame
from gridflow_gateway.iowa_dot import IowaDotCameraSource
from gridflow_gateway.local_detector import LocalRtdetrDetector
from gridflow_gateway.models import ReferenceCamera, ReferenceGatewaySettings, ReferenceObservation, VehicleClassCounts


def build_reference_observation(
    *,
    camera: ReferenceCamera,
    captured_at: datetime,
    class_counts: VehicleClassCounts,
    confidence: float,
    inference_ms: int,
    flow_delta_60s: float,
    detector_model: str = "PekingU/rtdetr_r50vd",
    detector_revision: str = "main",
) -> ReferenceObservation:
    return ReferenceObservation(
        source=camera,
        captured_at=captured_at,
        detector_model=detector_model,
        detector_revision=detector_revision,
        class_counts=class_counts,
        confidence=confidence,
        inference_ms=inference_ms,
        flow_delta_60s=flow_delta_60s,
    )


async def submit_reference_once(
    *,
    settings: ReferenceGatewaySettings,
    flow: RollingVehicleFlow,
    detector: LocalRtdetrDetector,
) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        camera = await IowaDotCameraSource(client).fetch(settings.source_id, settings.iowa_camera_id)
        image = await asyncio.to_thread(capture_video_frame, str(camera.video_url))
        summary, inference_ms = await asyncio.to_thread(detector.analyze_jpeg, image)
        captured_at = datetime.now(timezone.utc)
        observation = build_reference_observation(
            camera=camera,
            captured_at=captured_at,
            class_counts=summary.class_counts,
            confidence=summary.confidence,
            inference_ms=inference_ms,
            flow_delta_60s=flow.observe(total_vehicles=summary.class_counts.total, captured_at=captured_at),
            detector_model=settings.detector_model,
            detector_revision=settings.detector_revision,
        )
        return await ControlApiClient(settings, client).submit_reference(observation)


async def monitor_reference(
    *,
    settings: ReferenceGatewaySettings,
    once: bool,
    on_sample: Callable[[dict[str, Any]], None],
) -> None:
    flow = RollingVehicleFlow(window=timedelta(seconds=60))
    detector = LocalRtdetrDetector(
        model=settings.detector_model,
        revision=settings.detector_revision,
        threshold=settings.detector_threshold,
    )
    while True:
        recorded = await submit_reference_once(settings=settings, flow=flow, detector=detector)
        on_sample(recorded)
        if once:
            return
        await asyncio.sleep(settings.poll_interval_seconds)
