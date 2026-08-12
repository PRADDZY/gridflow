from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request, status
from pydantic import ValidationError

from risk import assess
from schemas import ControllerDecision, ControllerDecisionRequest, EventSnapshot, QueueObservation, Recommendation
from security import (
    require_controller_action_access,
    require_controller_read_access,
    require_signed_ingress,
)

app = FastAPI(
    title="GridFlow Control API",
    version="0.1.0",
    description="Produces human-approved queue-safety recommendations from signed observations.",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "gridflow-control-api"}


@app.post("/v1/observations", response_model=Recommendation)
async def create_recommendation(
    observation: QueueObservation,
    request: Request,
    _: None = Depends(require_signed_ingress),
) -> Recommendation:
    recommendation = assess(observation)
    event_state = _event_state(request, observation.event_id)
    if event_state is not None:
        await event_state.record(recommendation.model_dump(mode="json"))
    return recommendation


@app.get("/v1/events/{event_id}/current", response_model=EventSnapshot)
async def current_recommendation(
    event_id: str,
    request: Request,
    _: None = Depends(require_controller_read_access),
) -> EventSnapshot:
    event_state = _event_state(request, event_id)
    if event_state is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Durable event state is not available in this runtime.",
        )
    current = await event_state.current()
    if current is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No recommendation for this event.")
    return EventSnapshot.model_validate(current)


@app.post("/v1/events/{event_id}/decisions", response_model=EventSnapshot)
async def record_decision(
    event_id: str,
    decision_request: ControllerDecisionRequest,
    request: Request,
    _: None = Depends(require_controller_action_access),
) -> EventSnapshot:
    event_state = _event_state(request, event_id)
    if event_state is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Durable event state is not available in this runtime.",
        )

    controller_id = request.headers.get("x-gridflow-controller-id")
    if not controller_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing controller identity.")

    try:
        decision = ControllerDecision(
            event_id=event_id,
            recommendation_id=decision_request.recommendation_id,
            action=decision_request.action,
            controller_id=controller_id,
            note=decision_request.note,
            created_at=datetime.now(timezone.utc),
        )
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid controller identity.") from exc
    result = await event_state.decide(decision.model_dump(mode="json"))
    outcome = result.get("outcome")
    if outcome == "missing":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No recommendation for this event.")
    if outcome == "stale":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The active recommendation changed; review the newest observation.",
        )
    if outcome != "recorded" or "snapshot" not in result:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not persist the controller decision.",
        )
    return EventSnapshot.model_validate(result["snapshot"])


def _event_state(request: Request, event_id: str):
    env = request.scope.get("env")
    if env is None:
        return None
    try:
        return env.EVENT_STATE.getByName(event_id)
    except AttributeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Durable event state is not configured.",
        ) from exc
