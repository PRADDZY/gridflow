import { fetchIowaReferenceSource } from "@/lib/iowa-reference-source";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    return Response.json(await fetchIowaReferenceSource(), {
      headers: { "cache-control": "no-store" },
    });
  } catch {
    return Response.json(
      { detail: "The public reference camera metadata is unavailable." },
      { status: 502, headers: { "cache-control": "no-store" } },
    );
  }
}
