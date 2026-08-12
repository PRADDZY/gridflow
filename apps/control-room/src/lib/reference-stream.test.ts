import { describe, expect, it } from "vitest";
import { REFERENCE_HLS_CONFIG, fatalRecovery } from "@/lib/reference-stream";

describe("reference stream policy", () => {
  it("keeps the public low-latency HLS source near its live edge with bounded retries", () => {
    expect(REFERENCE_HLS_CONFIG.lowLatencyMode).toBe(true);
    expect(REFERENCE_HLS_CONFIG.liveSyncDuration).toBeGreaterThan(2);
    expect(REFERENCE_HLS_CONFIG.liveMaxLatencyDuration).toBeGreaterThan(REFERENCE_HLS_CONFIG.liveSyncDuration ?? 0);
    expect(REFERENCE_HLS_CONFIG.maxLiveSyncPlaybackRate).toBeGreaterThan(1);
    expect(REFERENCE_HLS_CONFIG.fragLoadPolicy?.default.errorRetry?.maxNumRetry).toBeGreaterThan(0);
  });

  it("retries one exhausted network load and recovers media decoding without a player reload", () => {
    expect(fatalRecovery("networkError", 0)).toBe("restart-load");
    expect(fatalRecovery("networkError", 1)).toBe("fail");
    expect(fatalRecovery("mediaError", 0)).toBe("recover-media");
    expect(fatalRecovery("otherError", 0)).toBe("fail");
  });
});
