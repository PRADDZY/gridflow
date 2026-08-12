import type { HlsConfig } from "hls.js";

const retry = {
  maxNumRetry: 4,
  retryDelayMs: 500,
  maxRetryDelayMs: 4_000,
  backoff: "exponential" as const,
};

const loadPolicy = {
  default: {
    maxTimeToFirstByteMs: 8_000,
    maxLoadTimeMs: 15_000,
    timeoutRetry: retry,
    errorRetry: retry,
  },
};

export const REFERENCE_HLS_CONFIG = {
  lowLatencyMode: true,
  liveSyncDuration: 3.2,
  liveMaxLatencyDuration: 9,
  maxLiveSyncPlaybackRate: 1.08,
  maxBufferLength: 15,
  backBufferLength: 30,
  maxBufferHole: 0.5,
  manifestLoadPolicy: loadPolicy,
  playlistLoadPolicy: loadPolicy,
  fragLoadPolicy: loadPolicy,
} satisfies Partial<HlsConfig>;

export type FatalRecovery = "restart-load" | "recover-media" | "fail";

export function fatalRecovery(errorType: string, networkRecoveryAttempts: number): FatalRecovery {
  if (errorType === "mediaError") return "recover-media";
  if (errorType === "networkError" && networkRecoveryAttempts === 0) return "restart-load";
  return "fail";
}
