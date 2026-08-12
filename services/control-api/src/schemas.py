from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


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
        pattern=r"^[a-z0-9][a-z0-9._-]+$",
    )
    note: str | None = Field(default=None, max_length=500)
    created_at: datetime


class EventSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommendation: Recommendation
    decision: ControllerDecision | None = None
