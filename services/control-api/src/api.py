from fastapi import Depends, FastAPI, HTTPException, Request, status

from risk import assess
from schemas import QueueObservation, Recommendation
from security import require_controller_read_access, require_signed_ingress

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


@app.get("/v1/events/{event_id}/current", response_model=Recommendation)
async def current_recommendation(
    event_id: str,
    request: Request,
    _: None = Depends(require_controller_read_access),
) -> Recommendation:
    event_state = _event_state(request, event_id)
    if event_state is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Durable event state is not available in this runtime.",
        )
    latest = await event_state.latest()
    if latest is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No recommendation for this event.")
    return Recommendation.model_validate(latest)


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
