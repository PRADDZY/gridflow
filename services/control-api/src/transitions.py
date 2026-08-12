from schemas import ControllerDecision, EventSnapshot, Recommendation


def start_recommendation(recommendation: Recommendation) -> EventSnapshot:
    """A fresh observation must invalidate approval for an older recommendation."""
    return EventSnapshot(recommendation=recommendation)


def record_controller_decision(
    snapshot: EventSnapshot,
    decision: ControllerDecision,
) -> EventSnapshot:
    if decision.event_id != snapshot.recommendation.event_id:
        raise ValueError("Decision event does not match the active recommendation.")
    if decision.recommendation_id != snapshot.recommendation.decision_id:
        raise ValueError("Decision does not match the active recommendation.")
    return snapshot.model_copy(update={"decision": decision})
