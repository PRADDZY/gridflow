import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ReferenceAnalytics } from "@/components/reference-analytics";
import type { ReferenceObservation, ReferenceSource } from "@/lib/reference-analytics";

vi.mock("@/components/reference-video-player", () => ({
  ReferenceVideoPlayer: ({ source }: { source: ReferenceSource | null }) => (
    <div data-testid="reference-video">{source?.camera_id ?? "no-source"}</div>
  ),
}));

vi.mock("@/components/venue-map", () => ({
  VenueMap: ({ mode }: { mode: string }) => <div data-testid="venue-map">{mode}</div>,
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

const observation: ReferenceObservation = {
  source,
  captured_at: "2026-08-12T08:00:00Z",
  detector_model: "PekingU/rtdetr_r50vd",
  detector_revision: "main",
  class_counts: { car: 14, truck: 2, bus: 1, motorcycle: 0 },
  confidence: 0.88,
  inference_ms: 342,
  flow_delta_60s: 4,
};

describe("ReferenceAnalytics", () => {
  it("uses the real navigation controls to switch among live, camera, map, and audit views", () => {
    const onRefresh = vi.fn();
    render(
      <ReferenceAnalytics
        source={source}
        observation={observation}
        history={[observation]}
        loading={false}
        error={null}
        onRefresh={onRefresh}
      />,
    );

    expect(screen.getByText("External reference analytics")).toBeInTheDocument();
    expect(screen.getByText("17")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Camera source" }));
    expect(screen.getByTestId("reference-video")).toHaveTextContent("DQTV17");
    expect(screen.getByRole("link", { name: "Open source stream" })).toHaveAttribute("href", source.video_url);

    fireEvent.click(screen.getByRole("button", { name: "Map" }));
    fireEvent.click(screen.getByRole("button", { name: "Reference camera location" }));
    expect(screen.getByTestId("venue-map")).toHaveTextContent("reference");

    fireEvent.click(screen.getByRole("button", { name: "Audit" }));
    expect(screen.getByText("Recent samples")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Refresh reference data" }));
    expect(onRefresh).toHaveBeenCalledOnce();
  });

  it("does not invent operational data when a source has no observation", () => {
    render(
      <ReferenceAnalytics
        source={source}
        observation={null}
        history={[]}
        loading={false}
        error={null}
        onRefresh={vi.fn()}
      />,
    );

    expect(screen.getByText("No reference observation received yet.")).toBeInTheDocument();
    expect(screen.queryByText("Approve and publish")).not.toBeInTheDocument();
    expect(screen.queryByText("Observed guests")).not.toBeInTheDocument();
  });
});
