"use client";

import Hls from "hls.js";
import { CircleAlert, Radio } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { ReferenceSource } from "@/lib/reference-analytics";

type PlayerState = "idle" | "loading" | "playing" | "error";

export function ReferenceVideoPlayer({ source }: { source: ReferenceSource | null }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [state, setState] = useState<PlayerState>("loading");
  const displayState = source ? state : "idle";

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !source) {
      return;
    }

    const initialState = window.setTimeout(() => setState("loading"), 0);
    let hls: Hls | undefined;
    const markPlaying = () => setState("playing");
    const markError = () => setState("error");
    video.addEventListener("playing", markPlaying);
    video.addEventListener("error", markError);

    if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = source.video_url;
      video.load();
    } else if (Hls.isSupported()) {
      hls = new Hls({ lowLatencyMode: true });
      hls.on(Hls.Events.ERROR, (_event, data) => {
        if (data.fatal) setState("error");
      });
      hls.loadSource(source.video_url);
      hls.attachMedia(video);
    } else {
      window.setTimeout(markError, 0);
    }

    return () => {
      video.removeEventListener("playing", markPlaying);
      video.removeEventListener("error", markError);
      window.clearTimeout(initialState);
      hls?.destroy();
      video.removeAttribute("src");
      video.load();
    };
  }, [source]);

  if (!source) {
    return <div className="video-empty">Source metadata is not available.</div>;
  }

  return (
    <div className="reference-video" data-state={displayState}>
      <video ref={videoRef} controls muted playsInline aria-label={`Live video from ${source.camera_id}`} />
      <div className="video-status" aria-live="polite">
        {displayState === "error" ? <CircleAlert size={15} /> : <Radio size={15} />}
        <span>{displayState === "error" ? "Playback unavailable" : `${source.camera_id} HLS stream`}</span>
      </div>
    </div>
  );
}
