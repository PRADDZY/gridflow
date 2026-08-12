from datetime import datetime
import os

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ModelEstimate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str = Field(min_length=3, max_length=128)
    revision: str = Field(min_length=3, max_length=128)
    people_count: int = Field(ge=0, le=100_000)
    confidence: float = Field(ge=0, le=1)
    inference_ms: int = Field(ge=0, le=120_000)


class QueueObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=3, max_length=80, pattern=r"^[a-z0-9-]+$")
    camera_id: str = Field(min_length=3, max_length=80, pattern=r"^[a-z0-9-]+$")
    zone_id: str = Field(min_length=3, max_length=80, pattern=r"^[a-z0-9-]+$")
    captured_at: datetime
    capacity: int = Field(ge=1, le=100_000)
    queue_change_per_minute: float = Field(ge=-10_000, le=10_000)
    detector: ModelEstimate
    density: ModelEstimate


class ControlApiSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    control_api_url: HttpUrl
    ingestion_hmac_secret: str = Field(min_length=16)


class GatewaySettings(ControlApiSettings):
    hf_token: str = Field(min_length=8)
    hf_detector_endpoint: HttpUrl
    hf_density_endpoint: HttpUrl
    detector_model: str = "PekingU/rtdetr_r50vd"
    detector_revision: str = "configured-endpoint"
    density_model: str = "venue-density-v1"
    density_revision: str = "configured-endpoint"

    @classmethod
    def from_environment(cls) -> "GatewaySettings":
        return cls(
            control_api_url=_require("CONTROL_API_URL"),
            ingestion_hmac_secret=_require("INGESTION_HMAC_SECRET"),
            hf_token=_require("HF_TOKEN"),
            hf_detector_endpoint=_require("HF_DETECTOR_ENDPOINT"),
            hf_density_endpoint=_require("HF_DENSITY_ENDPOINT"),
            detector_model=os.getenv("HF_DETECTOR_MODEL", "PekingU/rtdetr_r50vd"),
            detector_revision=os.getenv("HF_DETECTOR_REVISION", "configured-endpoint"),
            density_model=os.getenv("HF_DENSITY_MODEL", "venue-density-v1"),
            density_revision=os.getenv("HF_DENSITY_REVISION", "configured-endpoint"),
        )


class SyntheticGatewaySettings(ControlApiSettings):
    model_config = ConfigDict(extra="forbid")

    detector_model: str = "synthetic-person-detector"
    detector_revision: str = "demo-v1"
    density_model: str = "synthetic-density-estimator"
    density_revision: str = "demo-v1"

    @classmethod
    def from_environment(cls) -> "SyntheticGatewaySettings":
        return cls(
            control_api_url=_require("CONTROL_API_URL"),
            ingestion_hmac_secret=_require("INGESTION_HMAC_SECRET"),
        )


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} must be configured for the venue gateway.")
    return value
