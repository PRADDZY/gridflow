"use client";

import { useCallback, useEffect, useState } from "react";
import { ReferenceAnalytics } from "@/components/reference-analytics";
import type { ReferenceObservation, ReferenceSource } from "@/lib/reference-analytics";

type ReferenceData = {
  source: ReferenceSource | null;
  observation: ReferenceObservation | null;
  history: ReferenceObservation[];
};

export default function Home() {
  const [data, setData] = useState<ReferenceData>({ source: null, observation: null, history: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    const [sourceResult, currentResult, historyResult] = await Promise.allSettled([
      fetch("/api/reference/source", { cache: "no-store" }),
      fetch("/api/reference/current", { cache: "no-store" }),
      fetch("/api/reference/history", { cache: "no-store" }),
    ]);

    const source = await readJson<ReferenceSource>(sourceResult);
    const observation = await readJson<ReferenceObservation>(currentResult);
    const history = await readJson<ReferenceObservation[]>(historyResult);
    setData({ source: source.value, observation: observation.value, history: history.value ?? [] });
    const details = [source.detail, observation.detail, history.detail].filter((detail): detail is string => Boolean(detail));
    setError(details.length > 0 ? details[0] : null);
    setLoading(false);
  }, []);

  useEffect(() => {
    const initialRefresh = window.setTimeout(() => void refresh(), 0);
    const interval = window.setInterval(() => void refresh(), 10_000);
    return () => {
      window.clearTimeout(initialRefresh);
      window.clearInterval(interval);
    };
  }, [refresh]);

  return <ReferenceAnalytics {...data} loading={loading} error={error} onRefresh={() => void refresh()} />;
}

async function readJson<T>(result: PromiseSettledResult<Response>): Promise<{ value: T | null; detail: string | null }> {
  if (result.status === "rejected") return { value: null, detail: "Reference data could not be requested." };
  let body: unknown;
  try {
    body = await result.value.json();
  } catch {
    return { value: null, detail: "Reference service returned an invalid response." };
  }
  if (!result.value.ok) {
    const detail = body && typeof body === "object" && "detail" in body && typeof body.detail === "string"
      ? body.detail
      : "Reference data is currently unavailable.";
    return { value: null, detail };
  }
  return { value: body as T, detail: null };
}
