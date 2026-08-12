"use client";

import Hls from "hls.js";
import { CircleAlert, Radio } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { ReferenceSource } from "@/lib/reference-analytics";
import { fatalRecovery, REFERENCE_HLS_CONFIG } from "@/lib/reference-stream";

type PlayerState = "idle" | "loading" | "buffering" | "playing" | "error";

export function ReferenceVideoPlayer({ source }: { source: ReferenceSource | null }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [state, setState] = useState<PlayerState>("loading");
  const displayState = source ? state : "idle";
  const streamUrl = source?.video_url;

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !streamUrl) {
      return;
    }

    let disposed = false;
    let networkRecoveryAttempts = 0;
    let restartTimer: number | undefined;
    const initialState = window.setTimeout(() => setState("loading"), 0);
    let hls: Hls | undefined;
    const markPlaying = () => {
      networkRecoveryAttempts = 0;
      setState("playing");
    };
    const markBuffering = () => setState((current) => current === "error" ? current : "buffering");
    const markError = () => setState("error");
    const startPlayback = () => {
      const playAttempt = video.play();
      void playAttempt.catch(() => {
        // Muted autoplay is permitted in supported browsers; controls remain available otherwise.
      });
    };
    video.addEventListener("playing", markPlaying);
    video.addEventListener("canplay", startPlayback);
    video.addEventListener("waiting", markBuffering);
    video.addEventListener("stalled", markBuffering);
    video.addEventListener("error", markError);

    if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = streamUrl;
      video.load();
    } else if (Hls.isSupported()) {
      hls = new Hls(REFERENCE_HLS_CONFIG);
      hls.on(Hls.Events.MANIFEST_PARSED, startPlayback);
      hls.on(Hls.Events.ERROR, (_event, data) => {
        if (!data.fatal) return;

        const recovery = fatalRecovery(data.type, networkRecoveryAttempts);
        if (recovery === "recover-media") {
          markBuffering();
          hls?.recoverMediaError();
          return;
        }
        if (recovery === "restart-load") {
          networkRecoveryAttempts += 1;
          markBuffering();
          restartTimer = window.setTimeout(() => {
            if (!disposed) hls?.startLoad(-1);
          }, 1_500);
          return;
        }
        markError();
      });
      hls.loadSource(streamUrl);
      hls.attachMedia(video);
    } else {
      window.setTimeout(markError, 0);
    }

    return () => {
      video.removeEventListener("playing", markPlaying);
      video.removeEventListener("canplay", startPlayback);
      video.removeEventListener("waiting", markBuffering);
      video.removeEventListener("stalled", markBuffering);
      video.removeEventListener("error", markError);
      window.clearTimeout(initialState);
      if (restartTimer !== undefined) window.clearTimeout(restartTimer);
      disposed = true;
      hls?.destroy();
      video.removeAttribute("src");
      video.load();
    };
  }, [streamUrl]);

  if (!source) {
    return <div className="video-empty">Source metadata is not available.</div>;
  }

  return (
    <div className="reference-video" data-state={displayState}>
      <video ref={videoRef} autoPlay controls muted playsInline aria-label={`Live video from ${source.camera_id}`} />
      <div className="video-status" aria-live="polite">
        {displayState === "error" ? <CircleAlert size={15} /> : <Radio size={15} />}
        <span>{displayState === "error" ? "Playback unavailable" : displayState === "buffering" ? "Reconnecting to live edge" : `${source.camera_id} HLS stream`}</span>
      </div>
    </div>
  );
}
