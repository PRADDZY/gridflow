export type LiveRecommendation = {
  decision_id: string;
  risk: "stable" | "watch" | "critical" | "review";
  zone_id: string;
  estimated_people: number;
  capacity: number;
  queue_change_per_minute: number;
  confidence: number;
  model_agreement: number;
  camera_age_seconds: number;
  requires_human_approval: boolean;
  sign_action: string | null;
  steward_action: string | null;
  reason_codes: string[];
};

export type ControllerDecision = {
  decision_id: string;
  recommendation_id: string;
  action: "approve" | "hold";
  controller_id: string;
  created_at: string;
};

export type EventSnapshot = {
  recommendation: LiveRecommendation;
  decision: ControllerDecision | null;
};

export function hasPublishedSignAction(snapshot: EventSnapshot | null): boolean {
  return Boolean(
    snapshot?.decision?.action === "approve" &&
      snapshot.decision.recommendation_id === snapshot.recommendation.decision_id &&
      snapshot.recommendation.sign_action,
  );
}
