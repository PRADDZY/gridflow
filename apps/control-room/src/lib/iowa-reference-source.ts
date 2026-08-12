import type { ReferenceSource } from "@/lib/reference-analytics";

const IOWA_CAMERA_QUERY_URL =
  "https://services.arcgis.com/8lRhdTsQyJpO52F1/arcgis/rest/services/Traffic_Cameras_View/FeatureServer/0/query";

type IowaFeatureResponse = {
  features?: Array<{ attributes?: unknown }>;
};

export async function fetchIowaReferenceSource(): Promise<ReferenceSource> {
  const parameters = new URLSearchParams({
    f: "json",
    where: "COMMON_ID = 'DQTV17'",
    outFields: "COMMON_ID,Desc_,Route,VideoURL,latitude,longitude",
    returnGeometry: "false",
  });
  const response = await fetch(`${IOWA_CAMERA_QUERY_URL}?${parameters.toString()}`, {
    cache: "no-store",
    headers: { accept: "application/json" },
  });
  if (!response.ok) throw new Error("Iowa DOT source metadata is unavailable.");

  const payload = (await response.json()) as IowaFeatureResponse;
  if (!payload.features || payload.features.length !== 1) {
    throw new Error("Iowa DOT did not return the configured reference camera.");
  }
  return parseIowaReferenceSource(payload.features[0]?.attributes);
}

export function parseIowaReferenceSource(attributes: unknown): ReferenceSource {
  if (!attributes || typeof attributes !== "object" || Array.isArray(attributes)) {
    throw new Error("Iowa DOT returned invalid camera metadata.");
  }
  const values = attributes as Record<string, unknown>;
  const videoUrl = requiredText(values, "VideoURL");
  const parsedVideoUrl = new URL(videoUrl);
  if (
    parsedVideoUrl.protocol !== "https:" ||
    !(parsedVideoUrl.hostname === "iowadot.gov" || parsedVideoUrl.hostname.endsWith(".iowadot.gov"))
  ) {
    throw new Error("Iowa DOT returned an unapproved video host.");
  }

  const cameraId = requiredText(values, "COMMON_ID");
  if (cameraId !== "DQTV17") throw new Error("Iowa DOT returned metadata for a different camera.");

  return {
    source_id: "iowa-dq-dqtv17",
    source_mode: "external_reference",
    provider: "Iowa Department of Transportation",
    attribution: "Iowa Department of Transportation, CC BY 4.0",
    camera_id: cameraId,
    name: requiredText(values, "Desc_"),
    route: requiredText(values, "Route"),
    latitude: requiredCoordinate(values, "latitude", -90, 90),
    longitude: requiredCoordinate(values, "longitude", -180, 180),
    video_url: videoUrl,
  };
}

function requiredText(values: Record<string, unknown>, key: string): string {
  const value = values[key];
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new Error(`Iowa DOT metadata is missing ${key}.`);
  }
  return value.trim();
}

function requiredCoordinate(values: Record<string, unknown>, key: string, min: number, max: number): number {
  const value = values[key];
  const coordinate = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(coordinate) || coordinate < min || coordinate > max) {
    throw new Error(`Iowa DOT metadata has an invalid ${key}.`);
  }
  return coordinate;
}
