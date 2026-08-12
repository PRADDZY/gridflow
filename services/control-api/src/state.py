from workers import DurableObject

MAX_RECENT_RECOMMENDATIONS = 30


class EventState(DurableObject):
    async def record(self, recommendation: dict) -> None:
        history = await self.ctx.storage.get("history") or []
        history = [recommendation, *history][:MAX_RECENT_RECOMMENDATIONS]
        await self.ctx.storage.put("current", recommendation)
        await self.ctx.storage.put("history", history)

    async def latest(self) -> dict | None:
        return await self.ctx.storage.get("current")
