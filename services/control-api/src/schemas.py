from datetime import datetime
from typing import Literal
from urllib.parse import urlparse
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ModelEstimate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str = Field(min_length=3, max_length=128)
    revision: str = Field(min_length=3, max_length=128)
    people_count: int = Field(ge=0, le=100_000)
    confidence: float = Field(ge=0, le=1)
    inference_ms: int = Field(ge=0, le=120_000)


class QueueObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observation_id: UUID = Field(default_factory=uuid4)
    event_id: str = Field(min_length=3, max_length=80, pattern=r"^[a-z0-9-]+$")
    camera_id: str = Field(min_length=3, max_length=80, pattern=r"^[a-z0-9-]+$")
    zone_id: str = Field(min_length=3, max_length=80, pattern=r"^[a-z0-9-]+$")
    captured_at: datetime
    capacity: int = Field(ge=1, le=100_000)
    queue_change_per_minute: float = Field(ge=-10_000, le=10_000)
    detector: ModelEstimate
    density: ModelEstimate


class VehicleClassCounts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    car: int = Field(ge=0, le=100_000)
    truck: int = Field(ge=0, le=100_000)
    bus: int = Field(ge=0, le=100_000)
    motorcycle: int = Field(ge=0, le=100_000)

    @property
    def total(self) -> int:
        return self.car + self.truck + self.bus + self.motorcycle


class ReferenceSource(BaseModel):
    """A public camera used as an external analytics reference, never venue control input."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=3, max_length=80, pattern=r"^[a-z0-9-]+$")
    source_mode: Literal["external_reference"]
    provider: str = Field(min_length=3, max_length=160)
    attribution: str = Field(min_length=3, max_length=240)
    camera_id: str = Field(min_length=3, max_length=80)
    name: str = Field(min_length=3, max_length=240)
    route: str = Field(min_length=2, max_length=120)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    video_url: str = Field(min_length=12, max_length=2048)

    @field_validator("video_url")
    @classmethod
    def require_http_video_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("video_url must be an HTTPS URL.")
        return value


class ReferenceObservation(BaseModel):
    """A vehicle-only observation from an explicitly external public traffic camera."""

    model_config = ConfigDict(extra="forbid")

    source: ReferenceSource
    captured_at: datetime
    detector_model: str = Field(min_length=3, max_length=160)
    detector_revision: str = Field(min_length=1, max_length=160)
    class_counts: VehicleClassCounts
    confidence: float = Field(ge=0, le=1)
    inference_ms: int = Field(ge=0, le=120_000)
    flow_delta_60s: float = Field(ge=-100_000, le=100_000)


RiskLevel = Literal["stable", "watch", "critical", "review"]
DecisionAction = Literal["approve", "hold"]


class Recommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_id: UUID = Field(default_factory=uuid4)
    observation_id: UUID
    event_id: str
    camera_id: str
    zone_id: str
    created_at: datetime
    risk: RiskLevel
    estimated_people: int
    capacity: int
    occupancy_ratio: float
    queue_change_per_minute: float
    confidence: float
    model_agreement: float
    camera_age_seconds: float
    requires_human_approval: bool = True
    sign_action: str | None = None
    steward_action: str | None = None
    runbook: list[str]
    reason_codes: list[str]


class ControllerDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommendation_id: UUID
    action: DecisionAction
    note: str | None = Field(default=None, max_length=500)


class ControllerDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_id: UUID = Field(default_factory=uuid4)
    event_id: str = Field(min_length=3, max_length=80, pattern=r"^[a-z0-9-]+$")
    recommendation_id: UUID
    action: DecisionAction
    controller_id: str = Field(
        min_length=2,
        max_length=80,
        pattern=r"^[a-z0-9][a-z0-9@._+-]+$",
    )
    note: str | None = Field(default=None, max_length=500)
    created_at: datetime


class EventSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommendation: Recommendation
    decision: ControllerDecision | None = None
