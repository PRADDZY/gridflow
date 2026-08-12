import { fetchControlApi } from "@/lib/control-api";

export const dynamic = "force-dynamic";

const SOURCE_ID = "iowa-dq-dqtv17";

export async function GET() {
  const controllerToken = process.env.CONTROL_API_READ_TOKEN;
  if (!controllerToken) {
    return Response.json(
      { detail: "Reference observation access is not configured." },
      { status: 503, headers: { "cache-control": "no-store" } },
    );
  }

  try {
    const response = await fetchControlApi(`/v1/reference-sources/${SOURCE_ID}/history`, {
      cache: "no-store",
      headers: { "x-gridflow-controller-token": controllerToken },
    });
    return new Response(await response.text(), {
      status: response.status,
      headers: {
        "cache-control": "no-store",
        "content-type": response.headers.get("content-type") ?? "application/json",
      },
    });
  } catch {
    return Response.json(
      { detail: "Reference observation history is unavailable." },
      { status: 502, headers: { "cache-control": "no-store" } },
    );
  }
}
