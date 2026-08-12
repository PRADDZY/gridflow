from typing import Any

import httpx

from gridflow_gateway.models import ReferenceCamera


IOWA_DOT_CAMERA_QUERY_URL = (
    "https://services.arcgis.com/8lRhdTsQyJpO52F1/arcgis/rest/services/"
    "Traffic_Cameras_View/FeatureServer/0/query"
)
IOWA_DOT_ATTRIBUTION = "Iowa Department of Transportation, CC BY 4.0"


class PublicSourceError(RuntimeError):
    """The public metadata feed did not provide an approved, usable camera stream."""


class IowaDotCameraSource:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def fetch(self, source_id: str, camera_id: str) -> ReferenceCamera:
        response = await self._client.get(
            IOWA_DOT_CAMERA_QUERY_URL,
            params={
                "f": "json",
                "where": f"COMMON_ID = '{camera_id}'",
                "outFields": "COMMON_ID,device_id,Desc_,Route,UpdateDate,UpdateTime,ImageURL,VideoURL,latitude,longitude",
                "returnGeometry": "false",
            },
        )
        response.raise_for_status()
        payload = response.json()
        attributes = _single_attributes(payload)
        returned_camera_id = _required_text(attributes, "COMMON_ID")
        if returned_camera_id.casefold() != camera_id.casefold():
            raise PublicSourceError("Iowa DOT returned metadata for a different camera.")
        video_url = _required_text(attributes, "VideoURL")
        _require_iowa_dot_video_host(video_url)
        return ReferenceCamera(
            source_id=source_id,
            source_mode="external_reference",
            provider="Iowa Department of Transportation",
            attribution=IOWA_DOT_ATTRIBUTION,
            camera_id=returned_camera_id,
            name=_required_text(attributes, "Desc_"),
            route=_required_text(attributes, "Route"),
            latitude=attributes.get("latitude"),
            longitude=attributes.get("longitude"),
            video_url=video_url,
        )


def _single_attributes(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or not isinstance(payload.get("features"), list):
        raise PublicSourceError("Iowa DOT returned malformed camera metadata.")
    features = payload["features"]
    if len(features) != 1 or not isinstance(features[0], dict):
        raise PublicSourceError("Iowa DOT did not return exactly one requested camera.")
    attributes = features[0].get("attributes")
    if not isinstance(attributes, dict):
        raise PublicSourceError("Iowa DOT returned a camera without attributes.")
    return attributes


def _required_text(attributes: dict[str, Any], name: str) -> str:
    value = attributes.get(name)
    if not isinstance(value, str) or not value.strip():
        raise PublicSourceError(f"Iowa DOT camera metadata is missing {name}.")
    return value.strip()


def _require_iowa_dot_video_host(video_url: str) -> None:
    host = httpx.URL(video_url).host
    if host is None or not (host == "iowadot.gov" or host.endswith(".iowadot.gov")):
        raise PublicSourceError("Iowa DOT camera metadata returned an unapproved video host.")
