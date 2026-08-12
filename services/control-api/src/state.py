from workers import DurableObject

from schemas import ControllerDecision, EventSnapshot, Recommendation
from transitions import record_controller_decision, start_recommendation

MAX_RECENT_RECOMMENDATIONS = 30


class EventState(DurableObject):
    async def record(self, recommendation: dict) -> dict:
        snapshot = start_recommendation(Recommendation.model_validate(recommendation))
        serialized_snapshot = snapshot.model_dump(mode="json")
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
        await self.ctx.storage.put("current", serialized_snapshot)
        return {"outcome": "recorded", "snapshot": serialized_snapshot}
