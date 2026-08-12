from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

from fastapi import HTTPException
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from api import create_reference_observation, current_reference_observation, reference_history
from reference_history import record_reference_history
from schemas import ReferenceObservation, ReferenceSource, VehicleClassCounts


NOW = datetime(2026, 8, 12, 8, 0, tzinfo=timezone.utc)


def observation() -> ReferenceObservation:
    return ReferenceObservation(
        source=ReferenceSource(
            source_id="iowa-dq-dqtv17",
            source_mode="external_reference",
            provider="Iowa Department of Transportation",
            attribution="Iowa Department of Transportation, CC BY 4.0",
            camera_id="DQTV17",
            name="US 20 at MM 297.2 - JFK Rd - West",
            route="US 20",
            latitude=42.492226,
            longitude=-90.714405,
            video_url="https://video3.iowadot.gov:8888/cedarrapids/dqtv17lb/playlist.m3u8",
        ),
        captured_at=NOW,
        detector_model="PekingU/rtdetr_r50vd",
        detector_revision="main",
        class_counts=VehicleClassCounts(car=14, truck=2, bus=1, motorcycle=0),
        confidence=0.88,
        inference_ms=342,
        flow_delta_60s=4,
    )


class _ReferenceState:
    def __init__(self) -> None:
        self.current_value: dict | None = None
        self.history_value: list[dict] = []

    async def record(self, incoming: dict) -> dict:
        self.current_value = incoming
        self.history_value = [incoming, *self.history_value]
        return incoming

    async def current(self) -> dict | None:
        return self.current_value

    async def history(self) -> list[dict]:
        return self.history_value


class _ReferenceBinding:
    def __init__(self, state: _ReferenceState) -> None:
        self.state = state

    def getByName(self, source_id: str) -> _ReferenceState:
        if source_id != "iowa-dq-dqtv17":
            raise AssertionError(f"Unexpected source id: {source_id}")
        return self.state


class _Request:
    def __init__(self, state: _ReferenceState) -> None:
        self.scope = {"env": type("Env", (), {"REFERENCE_STATE": _ReferenceBinding(state)})()}


class ReferenceAnalyticsApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_signed_observation_is_persisted_under_its_reference_source(self) -> None:
        state = _ReferenceState()

        recorded = await create_reference_observation(
            "iowa-dq-dqtv17",
            observation(),
            _Request(state),
        )

        self.assertEqual(recorded.source.source_mode, "external_reference")
        self.assertEqual(recorded.class_counts.car, 14)
        self.assertEqual(state.current_value["source"]["camera_id"], "DQTV17")

    async def test_rejects_a_path_source_that_does_not_match_the_signed_payload(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            await create_reference_observation("another-camera", observation(), _Request(_ReferenceState()))

        self.assertEqual(raised.exception.status_code, 400)

    async def test_current_and_history_return_only_reference_observations(self) -> None:
        state = _ReferenceState()
        await create_reference_observation("iowa-dq-dqtv17", observation(), _Request(state))

        current = await current_reference_observation("iowa-dq-dqtv17", _Request(state))
        history = await reference_history("iowa-dq-dqtv17", _Request(state))

        self.assertEqual(current.source.camera_id, "DQTV17")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].flow_delta_60s, 4)


class ReferenceAnalyticsSchemaTests(unittest.TestCase):
    def test_reference_observation_forbids_venue_capacity_and_people_fields(self) -> None:
        payload = observation().model_dump(mode="json")
        payload["capacity"] = 500
        payload["people_count"] = 400

        with self.assertRaises(ValidationError):
            ReferenceObservation.model_validate(payload)


class ReferenceHistoryTests(unittest.TestCase):
    def test_reference_history_keeps_a_bounded_newest_first_history(self) -> None:
        history: list[dict] = []
        for index in range(65):
            incoming = observation().model_copy(update={"flow_delta_60s": index})
            history = record_reference_history(history, incoming.model_dump(mode="json"))

        self.assertEqual(len(history), 60)
        self.assertEqual(history[0]["flow_delta_60s"], 64)
        self.assertEqual(history[-1]["flow_delta_60s"], 5)
