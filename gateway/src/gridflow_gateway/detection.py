from dataclasses import dataclass
from typing import Any, Iterable

from gridflow_gateway.models import VehicleClassCounts


VEHICLE_LABELS = frozenset({"car", "truck", "bus", "motorcycle"})


@dataclass(frozen=True)
class VehicleDetectionSummary:
    class_counts: VehicleClassCounts
    confidence: float


def summarize_vehicle_detections(
    detections: Iterable[dict[str, Any]],
    *,
    threshold: float,
) -> VehicleDetectionSummary:
    counts = {label: 0 for label in VEHICLE_LABELS}
    accepted_scores: list[float] = []

    for detection in detections:
        label = detection.get("label")
        score = detection.get("score")
        if not isinstance(label, str) or not isinstance(score, (float, int)):
            continue
        normalized_label = label.casefold()
        normalized_score = float(score)
        if normalized_label not in VEHICLE_LABELS or not threshold <= normalized_score <= 1:
            continue
        counts[normalized_label] += 1
        accepted_scores.append(normalized_score)

    confidence = round(sum(accepted_scores) / len(accepted_scores), 3) if accepted_scores else 0.0
    return VehicleDetectionSummary(
        class_counts=VehicleClassCounts(**counts),
        confidence=confidence,
    )
