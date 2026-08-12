from fastapi import Depends, FastAPI, Request

from risk import assess
from schemas import QueueObservation, Recommendation
from security import require_signed_ingress

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
    return assess(observation)
