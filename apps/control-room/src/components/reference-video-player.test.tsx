import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ReferenceVideoPlayer } from "@/components/reference-video-player";
import type { ReferenceSource } from "@/lib/reference-analytics";

vi.mock("hls.js", () => ({
  default: {
    isSupported: () => false,
  },
}));

const source: ReferenceSource = {
  source_id: "iowa-dq-dqtv17",
  source_mode: "external_reference",
  provider: "Iowa Department of Transportation",
  attribution: "Iowa Department of Transportation, CC BY 4.0",
  camera_id: "DQTV17",
  name: "US 20 at MM 297.2 - JFK Rd - West",
  route: "US 20",
  latitude: 42.492226,
  longitude: -90.714405,
  video_url: "https://video3.iowadot.gov:8888/cedarrapids/dqtv17lb/playlist.m3u8",
};

describe("ReferenceVideoPlayer", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("requests muted autoplay so the live HLS stream starts without waiting for a click", () => {
    vi.spyOn(HTMLMediaElement.prototype, "load").mockImplementation(() => {});
    render(<ReferenceVideoPlayer source={source} />);

    const video = screen.getByLabelText("Live video from DQTV17");
    expect(video).toHaveAttribute("autoplay");
    expect(video).toHaveProperty("muted", true);
    expect(video).toHaveAttribute("playsinline");
  });

  it("keeps playback alive when analytics polling refreshes metadata for the same stream", () => {
    const load = vi.spyOn(HTMLMediaElement.prototype, "load").mockImplementation(() => {});
    vi.spyOn(HTMLMediaElement.prototype, "canPlayType").mockReturnValue("probably");
    const { rerender } = render(<ReferenceVideoPlayer source={source} />);

    expect(load).toHaveBeenCalledTimes(1);

    rerender(<ReferenceVideoPlayer source={{ ...source, name: "US 20 at JFK Rd" }} />);

    expect(load).toHaveBeenCalledTimes(1);
  });
});
