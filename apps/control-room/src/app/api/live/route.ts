import { controllerIdentity } from "@/lib/controller-access";

export const dynamic = "force-dynamic";

const EVENT_ID = "monza-2026";

export async function GET(request: Request) {
  const identity = await controllerIdentity(request);
  if (typeof identity !== "string") {
    return Response.json(
      { detail: identity.detail },
      { status: identity.status, headers: { "cache-control": "no-store" } },
    );
  }

  const controlApiUrl = process.env.CONTROL_API_URL;
  const controllerToken = process.env.CONTROL_API_READ_TOKEN;

  if (!controlApiUrl || !controllerToken) {
    return Response.json(
      { detail: "Live control API is not configured." },
      { status: 503, headers: { "cache-control": "no-store" } },
    );
  }

  try {
    const response = await fetch(
      `${controlApiUrl.replace(/\/$/, "")}/v1/events/${EVENT_ID}/current`,
      {
        cache: "no-store",
        headers: { "x-gridflow-controller-token": controllerToken },
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
    return Response.json(
      { detail: "Live control API is unavailable." },
      { status: 502, headers: { "cache-control": "no-store" } },
    );
  }
}
