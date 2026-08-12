import { describe, expect, it } from "vitest";
import { parseIowaReferenceSource } from "@/lib/iowa-reference-source";

const attributes = {
  COMMON_ID: "DQTV17",
  Desc_: "US 20 at MM 297.2 - JFK Rd - West",
  Route: "US 20",
  VideoURL: "https://video3.iowadot.gov:8888/cedarrapids/dqtv17lb/playlist.m3u8",
  latitude: 42.492226,
  longitude: -90.714405,
};

describe("parseIowaReferenceSource", () => {
  it("maps Iowa DOT metadata into the external-reference source contract", () => {
    const source = parseIowaReferenceSource(attributes);

    expect(source.source_mode).toBe("external_reference");
    expect(source.attribution).toContain("CC BY 4.0");
    expect(source.video_url).toBe(attributes.VideoURL);
  });

  it("rejects a camera stream that is not on an Iowa DOT host", () => {
    expect(() => parseIowaReferenceSource({ ...attributes, VideoURL: "https://invalid.example/live.m3u8" })).toThrow(
      "unapproved video host",
    );
  });
});
