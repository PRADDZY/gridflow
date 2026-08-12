from workers import DurableObject

from reference_history import record_reference_history
from schemas import ControllerDecision, EventSnapshot, Recommendation, ReferenceObservation
from transitions import record_controller_decision, record_observation

MAX_RECENT_RECOMMENDATIONS = 30
MAX_RECENT_DECISIONS = 100


class EventState(DurableObject):
    async def record(self, recommendation: dict) -> dict:
        current = await self.current()
        existing_snapshot = EventSnapshot.model_validate(current) if current else None
        snapshot = record_observation(existing_snapshot, Recommendation.model_validate(recommendation))
        serialized_snapshot = snapshot.model_dump(mode="json")
        if existing_snapshot is not None and snapshot is existing_snapshot:
            return serialized_snapshot

        history = await self.ctx.storage.get("history") or []
        history = [recommendation, *history][:MAX_RECENT_RECOMMENDATIONS]
        await self.ctx.storage.put("current", serialized_snapshot)
        await self.ctx.storage.put("history", history)
        return serialized_snapshot

    async def current(self) -> dict | None:
        return await self.ctx.storage.get("current")

    async def decide(self, decision: dict) -> dict:
        current = await self.current()
        if current is None:
            return {"outcome": "missing"}

        snapshot = EventSnapshot.model_validate(current)
        try:
            updated_snapshot = record_controller_decision(
                snapshot,
                ControllerDecision.model_validate(decision),
            )
        except ValueError:
            return {"outcome": "stale", "snapshot": current}

        serialized_snapshot = updated_snapshot.model_dump(mode="json")
        decisions = await self.ctx.storage.get("decision_history") or []
        decisions = [serialized_snapshot["decision"], *decisions][:MAX_RECENT_DECISIONS]
        await self.ctx.storage.put("current", serialized_snapshot)
        await self.ctx.storage.put("decision_history", decisions)
        return {"outcome": "recorded", "snapshot": serialized_snapshot}

    async def audit(self) -> list[dict]:
        return await self.ctx.storage.get("decision_history") or []


class ReferenceState(DurableObject):
    """Stores external reference observations separately from venue-risk state."""

    async def record(self, observation: dict) -> dict:
        serialized = ReferenceObservation.model_validate(observation).model_dump(mode="json")
        history = await self.ctx.storage.get("history") or []
        history = record_reference_history(history, serialized)
        await self.ctx.storage.put("current", serialized)
        await self.ctx.storage.put("history", history)
        return serialized

    async def current(self) -> dict | None:
        return await self.ctx.storage.get("current")

    async def history(self) -> list[dict]:
        return await self.ctx.storage.get("history") or []
