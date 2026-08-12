from datetime import datetime, timezone
from typing import Any

import httpx

from gridflow_gateway.control_api import ControlApiClient
from gridflow_gateway.huggingface import HuggingFaceVisionClient
from gridflow_gateway.models import GatewaySettings, ModelEstimate, QueueObservation, SyntheticGatewaySettings


async def analyze_and_submit(
    *,
    settings: GatewaySettings,
    image: bytes,
    event_id: str,
    camera_id: str,
    zone_id: str,
    capacity: int,
    queue_change_per_minute: float,
) -> dict[str, Any]:
    captured_at = datetime.now(timezone.utc)
    async with httpx.AsyncClient(timeout=20.0) as client:
        detector, density = await HuggingFaceVisionClient(settings, client).analyze(image)
        observation = QueueObservation(
            event_id=event_id,
            camera_id=camera_id,
            zone_id=zone_id,
            captured_at=captured_at,
            capacity=capacity,
            queue_change_per_minute=queue_change_per_minute,
            detector=detector,
            density=density,
        )
        return await ControlApiClient(settings, client).submit(observation)


async def submit_synthetic(
    *,
    settings: SyntheticGatewaySettings,
    event_id: str,
    camera_id: str,
    zone_id: str,
    capacity: int,
    queue_change_per_minute: float,
    detector_people: int,
    detector_confidence: float,
    density_people: int,
    density_confidence: float,
) -> dict[str, Any]:
    observation = QueueObservation(
        event_id=event_id,
        camera_id=camera_id,
        zone_id=zone_id,
        captured_at=datetime.now(timezone.utc),
        capacity=capacity,
        queue_change_per_minute=queue_change_per_minute,
        detector=ModelEstimate(
            model=settings.detector_model,
            revision=settings.detector_revision,
            people_count=detector_people,
            confidence=detector_confidence,
            inference_ms=0,
        ),
        density=ModelEstimate(
            model=settings.density_model,
            revision=settings.density_revision,
            people_count=density_people,
            confidence=density_confidence,
            inference_ms=0,
        ),
    )
    async with httpx.AsyncClient(timeout=20.0) as client:
        return await ControlApiClient(settings, client).submit(observation)
