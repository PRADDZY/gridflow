export type ReferenceSource = {
  source_id: string;
  source_mode: "external_reference";
  provider: string;
  attribution: string;
  camera_id: string;
  name: string;
  route: string;
  latitude: number;
  longitude: number;
  video_url: string;
};

export type VehicleClassCounts = {
  car: number;
  truck: number;
  bus: number;
  motorcycle: number;
};

export type ReferenceObservation = {
  source: ReferenceSource;
  captured_at: string;
  detector_model: string;
  detector_revision: string;
  class_counts: VehicleClassCounts;
  confidence: number;
  inference_ms: number;
  flow_delta_60s: number;
};

export function totalVehicles(counts: VehicleClassCounts): number {
  return counts.car + counts.truck + counts.bus + counts.motorcycle;
}

export function formatFlow(value: number): string {
  return `${value > 0 ? "+" : ""}${value}`;
}

export function formatTimestamp(value: string): string {
  const timestamp = new Date(value);
  if (Number.isNaN(timestamp.getTime())) return "Unavailable";
  return new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    timeZoneName: "short",
  }).format(timestamp);
}
