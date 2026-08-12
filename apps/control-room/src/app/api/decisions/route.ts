import { controllerIdentity } from "@/lib/controller-access";

export const dynamic = "force-dynamic";

const EVENT_ID = "monza-2026";

type DecisionInput = {
  recommendation_id: string;
  action: "approve" | "hold";
  note?: string;
};

export async function POST(request: Request) {
  const controlApiUrl = process.env.CONTROL_API_URL;
  const actionToken = process.env.CONTROL_API_ACTION_TOKEN;
  if (!controlApiUrl || !actionToken) {
    return jsonError(503, "Controller command delivery is not configured.");
  }

  const identity = await controllerIdentity(request);
  if (typeof identity !== "string") {
    return jsonError(identity.status, identity.detail);
  }

  const input = await decisionInput(request);
  if (typeof input === "string") {
    return jsonError(400, input);
  }

  try {
    const response = await fetch(
      `${controlApiUrl.replace(/\/$/, "")}/v1/events/${EVENT_ID}/decisions`,
      {
        method: "POST",
        cache: "no-store",
        headers: {
          "content-type": "application/json",
          "x-gridflow-controller-token": actionToken,
          "x-gridflow-controller-id": identity,
        },
        body: JSON.stringify(input),
      },
    );
    const body = await response.text();
    return new Response(body, {
      status: response.status,
      headers: {
        "cache-control": "no-store",
        "content-type": response.headers.get("content-type") ?? "application/json",
      },
    });
  } catch {
    return jsonError(502, "Controller command delivery is unavailable.");
  }
}

async function decisionInput(request: Request): Promise<DecisionInput | string> {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return "A JSON controller decision is required.";
  }

  if (!body || typeof body !== "object" || Array.isArray(body)) {
    return "A valid controller decision is required.";
  }
  const value = body as Record<string, unknown>;
  if (typeof value.recommendation_id !== "string" || value.recommendation_id.length === 0) {
    return "A recommendation identifier is required.";
  }
  if (value.action !== "approve" && value.action !== "hold") {
    return "A valid controller action is required.";
  }
  if (value.note !== undefined && (typeof value.note !== "string" || value.note.length > 500)) {
    return "The controller note is invalid.";
  }
  return {
    recommendation_id: value.recommendation_id,
    action: value.action,
    ...(typeof value.note === "string" ? { note: value.note } : {}),
  };
}

function jsonError(status: number, detail: string) {
  return Response.json({ detail }, { status, headers: { "cache-control": "no-store" } });
}
