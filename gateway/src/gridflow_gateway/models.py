from datetime import datetime
import os
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class VehicleClassCounts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    car: int = Field(ge=0, le=100_000)
    truck: int = Field(ge=0, le=100_000)
    bus: int = Field(ge=0, le=100_000)
    motorcycle: int = Field(ge=0, le=100_000)

    @property
    def total(self) -> int:
        return self.car + self.truck + self.bus + self.motorcycle


class ReferenceCamera(BaseModel):
    """Public traffic-camera metadata for the external reference analytics mode."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=3, max_length=80, pattern=r"^[a-z0-9-]+$")
    source_mode: Literal["external_reference"] = "external_reference"
    provider: str = Field(min_length=3, max_length=160)
    attribution: str = Field(min_length=3, max_length=240)
    camera_id: str = Field(min_length=3, max_length=80)
    name: str = Field(min_length=3, max_length=240)
    route: str = Field(min_length=2, max_length=120)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    video_url: HttpUrl


class ReferenceObservation(BaseModel):
    """Vehicle-only public-camera observation; it cannot describe venue operations."""

    model_config = ConfigDict(extra="forbid")

    source: ReferenceCamera
    captured_at: datetime
    detector_model: str = Field(min_length=3, max_length=160)
    detector_revision: str = Field(min_length=1, max_length=160)
    class_counts: VehicleClassCounts
    confidence: float = Field(ge=0, le=1)
    inference_ms: int = Field(ge=0, le=120_000)
    flow_delta_60s: float = Field(ge=-100_000, le=100_000)


class ControlApiSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    control_api_url: HttpUrl
    ingestion_hmac_secret: str = Field(min_length=16)


class ReferenceGatewaySettings(ControlApiSettings):
    source_id: str = "iowa-dq-dqtv17"
    iowa_camera_id: str = "DQTV17"
    detector_model: str = "PekingU/rtdetr_r50vd"
    detector_revision: str = "main"
    detector_threshold: float = Field(default=0.5, ge=0, le=1)
    poll_interval_seconds: int = Field(default=10, ge=5, le=300)

    @classmethod
    def from_environment(cls) -> "ReferenceGatewaySettings":
        return cls(
            control_api_url=_require("CONTROL_API_URL"),
            ingestion_hmac_secret=_require("INGESTION_HMAC_SECRET"),
            source_id=os.getenv("REFERENCE_SOURCE_ID", "iowa-dq-dqtv17"),
            iowa_camera_id=os.getenv("IOWA_CAMERA_ID", "DQTV17"),
            detector_model=os.getenv("DETECTOR_MODEL", "PekingU/rtdetr_r50vd"),
            detector_revision=os.getenv("DETECTOR_REVISION", "main"),
            detector_threshold=float(os.getenv("DETECTOR_THRESHOLD", "0.5")),
            poll_interval_seconds=int(os.getenv("POLL_INTERVAL_SECONDS", "10")),
        )


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} must be configured for the reference analytics gateway.")
    return value
