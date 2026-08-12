import { type EventSnapshot } from "@/lib/live-state";
import { signageForSnapshot } from "@/lib/signage";

export const dynamic = "force-dynamic";

const EVENT_ID = "monza-2026";

export async function GET() {
  const controlApiUrl = process.env.CONTROL_API_URL;
  const controllerToken = process.env.CONTROL_API_READ_TOKEN;
  if (!controlApiUrl || !controllerToken) {
    return pendingSignage();
  }

  try {
    const response = await fetch(
      `${controlApiUrl.replace(/\/$/, "")}/v1/events/${EVENT_ID}/current`,
      {
        cache: "no-store",
        headers: { "x-gridflow-controller-token": controllerToken },
      },
    );
    if (!response.ok) return pendingSignage();
    const snapshot = (await response.json()) as EventSnapshot;
    return Response.json(signageForSnapshot(snapshot), {
      headers: { "cache-control": "no-store" },
    });
  } catch {
    return pendingSignage();
  }
}

function pendingSignage() {
  return Response.json({ state: "pending" }, { headers: { "cache-control": "no-store" } });
}
