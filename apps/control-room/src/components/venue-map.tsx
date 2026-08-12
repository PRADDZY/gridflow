"use client";

import { Map as MapLibreMap, Marker, NavigationControl, Popup } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef, useState } from "react";
import type { ReferenceSource } from "@/lib/reference-analytics";

const MONZA_CENTER: [number, number] = [9.2893, 45.6202];
const OPEN_FREE_MAP_STYLE = "https://tiles.openfreemap.org/styles/liberty";

type VenueMapProps = {
  mode: "venue" | "reference";
  source: ReferenceSource | null;
};

export function VenueMap({ mode, source }: VenueMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const markerRef = useRef<Marker | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new MapLibreMap({
      container: containerRef.current,
      style: OPEN_FREE_MAP_STYLE,
      center: MONZA_CENTER,
      zoom: 13.4,
    });
    map.addControl(new NavigationControl({ showCompass: false }), "top-right");
    map.on("load", () => {
      map.resize();
      setReady(true);
    });
    mapRef.current = map;
    const resizeObserver = typeof ResizeObserver === "undefined"
      ? null
      : new ResizeObserver(() => map.resize());
    resizeObserver?.observe(containerRef.current);

    return () => {
      resizeObserver?.disconnect();
      markerRef.current?.remove();
      markerRef.current = null;
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;

    if (mode === "venue") {
      markerRef.current?.remove();
      markerRef.current = null;
      map.jumpTo({ center: MONZA_CENTER, zoom: 13.4 });
      return;
    }

    if (!source) return;
    markerRef.current?.remove();
    markerRef.current = new Marker({ color: "#f05b4f" })
      .setLngLat([source.longitude, source.latitude])
      .setPopup(new Popup({ offset: 18 }).setText(`${source.provider}: ${source.camera_id}`))
      .addTo(map);
    map.jumpTo({ center: [source.longitude, source.latitude], zoom: 14.2 });
  }, [mode, ready, source]);

  return <div className="map-canvas" ref={containerRef} aria-label="Geographic reference map" />;
}
