from typing import Any

import httpx

from gridflow_gateway.models import ControlApiSettings, QueueObservation
from gridflow_gateway.signing import compact_json, signed_headers


class ControlApiClient:
    def __init__(self, settings: ControlApiSettings, client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._client = client

    async def submit(self, observation: QueueObservation) -> dict[str, Any]:
        body = compact_json(observation.model_dump(mode="json"))
        response = await self._client.post(
            str(self._settings.control_api_url).rstrip("/") + "/v1/observations",
            content=body,
            headers=signed_headers(body, self._settings.ingestion_hmac_secret),
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError("Control API returned a malformed recommendation.")
        return payload
