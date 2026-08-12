from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from schemas import ControllerDecision, Recommendation
from transitions import record_controller_decision, record_observation, start_recommendation


NOW = datetime(2026, 8, 12, 8, 0, tzinfo=timezone.utc)


def recommendation() -> Recommendation:
    return Recommendation(
        observation_id=uuid4(),
        event_id="monza-2026",
        camera_id="cam-04",
        zone_id="south-exit",
        created_at=NOW,
        risk="critical",
        estimated_people=436,
        capacity=520,
        occupancy_ratio=0.838,
        queue_change_per_minute=18,
        confidence=0.88,
        model_agreement=0.98,
        camera_age_seconds=4,
        sign_action="Publish Blue Route diversion to approved displays.",
        steward_action="Assign two stewards to hold new arrivals and open the Blue Route.",
        runbook=["Verify the live camera view with the zone lead."],
        reason_codes=["occupancy_critical"],
    )


class ControllerDecisionTransitionTests(unittest.TestCase):
    def test_matching_approval_is_attached_to_active_recommendation(self) -> None:
        active_recommendation = recommendation()
        decision = ControllerDecision(
            event_id=active_recommendation.event_id,
            recommendation_id=active_recommendation.decision_id,
            action="approve",
            controller_id="a.kapoor@gridflow.example",
            created_at=NOW,
        )

        snapshot = record_controller_decision(start_recommendation(active_recommendation), decision)

        self.assertEqual(snapshot.decision, decision)

    def test_new_recommendation_clears_previous_approval(self) -> None:
        previous_recommendation = recommendation()
        approved_snapshot = record_controller_decision(
            start_recommendation(previous_recommendation),
            ControllerDecision(
                event_id=previous_recommendation.event_id,
                recommendation_id=previous_recommendation.decision_id,
                action="approve",
                controller_id="a.kapoor@gridflow.example",
                created_at=NOW,
            ),
        )

        refreshed_snapshot = start_recommendation(recommendation())

        self.assertIsNotNone(approved_snapshot.decision)
        self.assertIsNone(refreshed_snapshot.decision)

    def test_replayed_observation_keeps_its_existing_approval(self) -> None:
        observed_recommendation = recommendation()
        approved_snapshot = record_controller_decision(
            start_recommendation(observed_recommendation),
            ControllerDecision(
                event_id=observed_recommendation.event_id,
                recommendation_id=observed_recommendation.decision_id,
                action="approve",
                controller_id="a.kapoor@gridflow.example",
                created_at=NOW,
            ),
        )
        retry = observed_recommendation.model_copy(update={"decision_id": uuid4()})

        retried_snapshot = record_observation(approved_snapshot, retry)

        self.assertEqual(retried_snapshot, approved_snapshot)

    def test_rejects_a_decision_for_an_older_recommendation(self) -> None:
        old_recommendation = recommendation()
        active_snapshot = start_recommendation(recommendation())
        stale_decision = ControllerDecision(
            event_id=old_recommendation.event_id,
            recommendation_id=old_recommendation.decision_id,
            action="approve",
            controller_id="a.kapoor@gridflow.example",
            created_at=NOW,
        )

        with self.assertRaises(ValueError):
            record_controller_decision(active_snapshot, stale_decision)
