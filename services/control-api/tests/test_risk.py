from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from risk import assess
from schemas import ModelEstimate, QueueObservation


NOW = datetime(2026, 8, 12, 8, 0, tzinfo=timezone.utc)


def observation(**overrides: object) -> QueueObservation:
    values: dict[str, object] = {
        "event_id": "monza-2026",
        "camera_id": "cam-04",
        "zone_id": "south-exit",
        "captured_at": NOW - timedelta(seconds=4),
        "capacity": 520,
        "queue_change_per_minute": 18,
        "detector": ModelEstimate(
            model="PekingU/rtdetr_r50vd",
            revision="3a744ea",
            people_count=432,
            confidence=0.93,
            inference_ms=240,
        ),
        "density": ModelEstimate(
            model="venue-density-v1",
            revision="7d90c11",
            people_count=440,
            confidence=0.90,
            inference_ms=188,
        ),
    }
    values.update(overrides)
    return QueueObservation(**values)


class RiskAssessmentTests(unittest.TestCase):
    def test_critical_queue_requires_human_approval(self) -> None:
        result = assess(observation(), now=NOW)

        self.assertEqual(result.risk, "critical")
        self.assertTrue(result.requires_human_approval)
        self.assertIsNotNone(result.sign_action)
        self.assertIn("occupancy_critical", result.reason_codes)

    def test_stale_camera_is_review_not_critical(self) -> None:
        result = assess(observation(captured_at=NOW - timedelta(seconds=30)), now=NOW)

        self.assertEqual(result.risk, "review")
        self.assertIn("camera_stale", result.reason_codes)
        self.assertIsNone(result.sign_action)

    def test_model_disagreement_is_review_not_critical(self) -> None:
        result = assess(
            observation(
                density=ModelEstimate(
                    model="venue-density-v1",
                    revision="7d90c11",
                    people_count=120,
                    confidence=0.91,
                    inference_ms=188,
                )
            ),
            now=NOW,
        )

        self.assertEqual(result.risk, "review")
        self.assertIn("model_disagreement", result.reason_codes)
        self.assertIsNone(result.sign_action)

    def test_low_confidence_is_review(self) -> None:
        result = assess(
            observation(
                detector=ModelEstimate(
                    model="PekingU/rtdetr_r50vd",
                    revision="3a744ea",
                    people_count=432,
                    confidence=0.42,
                    inference_ms=240,
                )
            ),
            now=NOW,
        )

        self.assertEqual(result.risk, "review")
        self.assertIn("model_confidence_low", result.reason_codes)
