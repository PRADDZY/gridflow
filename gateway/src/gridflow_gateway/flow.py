from collections import deque
from datetime import datetime, timedelta


class RollingVehicleFlow:
    def __init__(self, *, window: timedelta) -> None:
        self._window = window
        self._observations: deque[tuple[datetime, int]] = deque()

    def observe(self, *, total_vehicles: int, captured_at: datetime) -> int:
        self._observations.append((captured_at, total_vehicles))
        cutoff = captured_at - self._window
        while self._observations and self._observations[0][0] < cutoff:
            self._observations.popleft()

        return total_vehicles - self._observations[0][1]
