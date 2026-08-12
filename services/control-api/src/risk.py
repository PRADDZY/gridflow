from dataclasses import dataclass
from datetime import datetime, timezone

from schemas import QueueObservation, Recommendation

MIN_MODEL_CONFIDENCE = 0.70
MIN_MODEL_AGREEMENT = 0.75
STALE_CAMERA_SECONDS = 25


@dataclass(frozen=True)
class AssessmentInputs:
    estimated_people: int
    model_agreement: float
    confidence: float
    camera_age_seconds: float


def assess(observation: QueueObservation, now: datetime | None = None) -> Recommendation:
    evaluated_at = now or datetime.now(timezone.utc)
    captured_at = _as_utc(observation.captured_at)
    camera_age_seconds = max(0.0, (evaluated_at - captured_at).total_seconds())
    inputs = _assessment_inputs(observation, camera_age_seconds)
    risk, reason_codes = _classify(observation, inputs)
    sign_action, steward_action, runbook = _runbook(risk)

    return Recommendation(
        observation_id=observation.observation_id,
        event_id=observation.event_id,
        camera_id=observation.camera_id,
        zone_id=observation.zone_id,
        created_at=evaluated_at,
        risk=risk,
        estimated_people=inputs.estimated_people,
        capacity=observation.capacity,
        occupancy_ratio=round(inputs.estimated_people / observation.capacity, 3),
        queue_change_per_minute=observation.queue_change_per_minute,
        confidence=round(inputs.confidence, 3),
        model_agreement=round(inputs.model_agreement, 3),
        camera_age_seconds=round(inputs.camera_age_seconds, 1),
        sign_action=sign_action,
        steward_action=steward_action,
        runbook=runbook,
        reason_codes=reason_codes,
    )


def _assessment_inputs(observation: QueueObservation, camera_age_seconds: float) -> AssessmentInputs:
    detector_weight = observation.detector.confidence
    density_weight = observation.density.confidence
    total_weight = detector_weight + density_weight
    estimated_people = round(
        (observation.detector.people_count * detector_weight + observation.density.people_count * density_weight)
        / total_weight
    ) if total_weight else max(observation.detector.people_count, observation.density.people_count)

    largest_count = max(observation.detector.people_count, observation.density.people_count, 1)
    model_agreement = 1 - abs(observation.detector.people_count - observation.density.people_count) / largest_count
    freshness_factor = max(0.0, 1 - camera_age_seconds / STALE_CAMERA_SECONDS)
    confidence = min(observation.detector.confidence, observation.density.confidence) * model_agreement * freshness_factor

    return AssessmentInputs(
        estimated_people=estimated_people,
        model_agreement=model_agreement,
        confidence=confidence,
        camera_age_seconds=camera_age_seconds,
    )


def _classify(observation: QueueObservation, inputs: AssessmentInputs) -> tuple[str, list[str]]:
    reason_codes: list[str] = []
    if inputs.camera_age_seconds > STALE_CAMERA_SECONDS:
        reason_codes.append("camera_stale")
    if min(observation.detector.confidence, observation.density.confidence) < MIN_MODEL_CONFIDENCE:
        reason_codes.append("model_confidence_low")
    if inputs.model_agreement < MIN_MODEL_AGREEMENT:
        reason_codes.append("model_disagreement")
    if reason_codes:
        return "review", reason_codes

    occupancy = inputs.estimated_people / observation.capacity
    if occupancy >= 0.80 and observation.queue_change_per_minute >= 10:
        return "critical", ["occupancy_critical", "queue_growth_high"]
    if occupancy >= 0.60 or observation.queue_change_per_minute >= 5:
        return "watch", ["occupancy_elevated" if occupancy >= 0.60 else "queue_growth_elevated"]
    return "stable", ["within_operating_range"]


def _runbook(risk: str) -> tuple[str | None, str | None, list[str]]:
    if risk == "critical":
        return (
            "Publish Blue Route diversion to approved displays.",
            "Assign two stewards to hold new arrivals and open the Blue Route.",
            [
                "Verify the live camera view with the zone lead.",
                "Request two stewards at the queue head.",
                "Approve the Blue Route display update.",
                "Reassess after the next confirmed observation.",
            ],
        )
    if risk == "watch":
        return (
            None,
            "Stage one steward at the queue head and confirm egress capacity.",
            [
                "Confirm the camera view is unobstructed.",
                "Notify the zone lead of the elevated queue.",
                "Reassess after the next confirmed observation.",
            ],
        )
    if risk == "review":
        return (
            None,
            "Validate the live camera view before directing staff or signage.",
            [
                "Inspect camera health and the live CCTV frame.",
                "Compare the observation with the zone lead's report.",
                "Do not publish a diversion until a controller approves it.",
            ],
        )
    return (None, None, ["Continue routine monitoring."])


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
