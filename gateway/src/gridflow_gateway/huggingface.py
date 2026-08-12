import asyncio
import time
from typing import Any

import httpx

from gridflow_gateway.models import GatewaySettings, ModelEstimate


class InferenceResponseError(RuntimeError):
    """Raised when an inference endpoint returns a result GridFlow cannot trust."""


class HuggingFaceVisionClient:
    def __init__(self, settings: GatewaySettings, client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._client = client

    async def analyze(self, image: bytes) -> tuple[ModelEstimate, ModelEstimate]:
        detector_response, density_response = await asyncio.gather(
            self._post_image(str(self._settings.hf_detector_endpoint), image),
            self._post_image(str(self._settings.hf_density_endpoint), image),
        )
        return (
            self._parse_detector(detector_response),
            self._parse_density(density_response),
        )

    async def _post_image(self, endpoint: str, image: bytes) -> tuple[Any, int]:
        started = time.perf_counter()
        response = await self._client.post(
            endpoint,
            content=image,
            headers={
                "authorization": f"Bearer {self._settings.hf_token}",
                "content-type": "image/jpeg",
            },
        )
        response.raise_for_status()
        return response.json(), round((time.perf_counter() - started) * 1000)

    def _parse_detector(self, response: tuple[Any, int]) -> ModelEstimate:
        payload, inference_ms = response
        if not isinstance(payload, list):
            raise InferenceResponseError("Detector endpoint must return a list of detections.")

        people_scores: list[float] = []
        for detection in payload:
            if not isinstance(detection, dict):
                raise InferenceResponseError("Detector endpoint returned an invalid detection.")
            if detection.get("label", "").casefold() == "person":
                score = detection.get("score")
                if not isinstance(score, (float, int)) or not 0 <= score <= 1:
                    raise InferenceResponseError("Detector endpoint returned an invalid person confidence.")
                people_scores.append(float(score))

        confidence = round(sum(people_scores) / len(people_scores), 3) if people_scores else 1.0
        return ModelEstimate(
            model=self._settings.detector_model,
            revision=self._settings.detector_revision,
            people_count=len(people_scores),
            confidence=confidence,
            inference_ms=inference_ms,
        )

    def _parse_density(self, response: tuple[Any, int]) -> ModelEstimate:
        payload, inference_ms = response
        if not isinstance(payload, dict):
            raise InferenceResponseError("Density endpoint must return an object.")
        people_count = payload.get("people_count")
        confidence = payload.get("confidence")
        if not isinstance(people_count, int) or people_count < 0:
            raise InferenceResponseError("Density endpoint returned an invalid people count.")
        if not isinstance(confidence, (float, int)) or not 0 <= confidence <= 1:
            raise InferenceResponseError("Density endpoint returned an invalid confidence.")
        return ModelEstimate(
            model=self._settings.density_model,
            revision=self._settings.density_revision,
            people_count=people_count,
            confidence=float(confidence),
            inference_ms=inference_ms,
        )
