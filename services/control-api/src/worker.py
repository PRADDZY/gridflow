from workers import WorkerEntrypoint

from api import app
from state import EventState, ReferenceState


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        import asgi

        return await asgi.fetch(app, request.js_object, self.env)
