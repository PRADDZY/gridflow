"use client";

import {
  Activity,
  Camera,
  ClipboardList,
  ExternalLink,
  Map,
  MapPinned,
  RefreshCw,
  Route,
  ScanLine,
} from "lucide-react";
import { useMemo, useState } from "react";
import { ReferenceVideoPlayer } from "@/components/reference-video-player";
import { VenueMap } from "@/components/venue-map";
import {
  formatFlow,
  formatTimestamp,
  totalVehicles,
  type ReferenceObservation,
  type ReferenceSource,
} from "@/lib/reference-analytics";

type View = "live" | "camera" | "map" | "audit";
type MapMode = "venue" | "reference";

type ReferenceAnalyticsProps = {
  source: ReferenceSource | null;
  observation: ReferenceObservation | null;
  history: ReferenceObservation[];
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
};

const navigation: Array<{ id: View; label: string; icon: typeof Activity }> = [
  { id: "live", label: "Live board", icon: Activity },
  { id: "camera", label: "Camera source", icon: Camera },
  { id: "map", label: "Map", icon: Map },
  { id: "audit", label: "Audit", icon: ClipboardList },
];

export function ReferenceAnalytics({
  source,
  observation,
  history,
  loading,
  error,
  onRefresh,
}: ReferenceAnalyticsProps) {
  const [view, setView] = useState<View>("live");
  const [mapMode, setMapMode] = useState<MapMode>("venue");
  const sourceForVideo = observation?.source ?? source;

  const sourceTitle = useMemo(() => {
    if (!sourceForVideo) return "Reference source unavailable";
    return `${sourceForVideo.camera_id} / ${sourceForVideo.route}`;
  }, [sourceForVideo]);

  return (
    <main className="control-shell">
      <aside className="control-rail" aria-label="Reference analytics navigation">
        <div className="brand-lockup">
          <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>
          <div><p>GRIDFLOW</p><strong>Reference</strong></div>
        </div>
        <nav className="control-nav">
          {navigation.map(({ id, label, icon: Icon }) => (
            <button
              className={view === id ? "nav-control is-active" : "nav-control"}
              key={id}
              onClick={() => setView(id)}
              type="button"
            >
              <Icon size={18} />
              <span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="rail-source-status"><span /> External source only</div>
      </aside>

      <section className="control-workspace">
        <header className="control-header">
          <div>
            <p className="eyebrow">Grand Prix egress context</p>
            <h1>External reference analytics</h1>
          </div>
          <button className="icon-control" onClick={onRefresh} type="button" aria-label="Refresh reference data" title="Refresh reference data">
            <RefreshCw size={18} className={loading ? "is-spinning" : undefined} />
          </button>
        </header>

        <section className="reference-boundary" aria-label="Reference source boundary">
          <Route size={18} />
          <div>
            <strong>{sourceTitle}</strong>
            <span>{sourceForVideo ? `${sourceForVideo.provider} | ${sourceForVideo.attribution}` : "No venue-control data is shown here."}</span>
          </div>
        </section>

        {error ? <p className="data-error" role="alert">{error}</p> : null}
        {view === "live" ? (
          <LiveView observation={observation} source={sourceForVideo} mapMode={mapMode} onMapModeChange={setMapMode} />
        ) : null}
        {view === "camera" ? <CameraView source={sourceForVideo} /> : null}
        {view === "map" ? <MapView source={sourceForVideo} mode={mapMode} onModeChange={setMapMode} /> : null}
        {view === "audit" ? <AuditView history={history} /> : null}
      </section>
    </main>
  );
}

function LiveView({
  observation,
  source,
  mapMode,
  onMapModeChange,
}: {
  observation: ReferenceObservation | null;
  source: ReferenceSource | null;
  mapMode: MapMode;
  onMapModeChange: (mode: MapMode) => void;
}) {
  const vehicleTotal = observation ? totalVehicles(observation.class_counts) : null;
  return (
    <>
      <section className="metric-strip" aria-label="Current reference sample">
        <Metric label="Vehicles" value={vehicleTotal === null ? "--" : String(vehicleTotal)} detail="Current frame" icon={<Activity size={18} />} />
        <Metric label="Flow delta" value={observation ? formatFlow(observation.flow_delta_60s) : "--"} detail="Rolling 60 seconds" icon={<Route size={18} />} />
        <Metric label="Detector confidence" value={observation ? `${Math.round(observation.confidence * 100)}%` : "--"} detail="Vehicle classes only" icon={<ScanLine size={18} />} />
        <Metric label="Inference" value={observation ? `${observation.inference_ms} ms` : "--"} detail="Local RT-DETR" icon={<Camera size={18} />} />
      </section>

      <div className="analytics-grid">
        <section className="surface video-surface" aria-labelledby="live-video-heading">
          <SurfaceHeading eyebrow="Live HLS" heading="Public traffic camera" />
          <ReferenceVideoPlayer source={source} />
          <SourceMeta source={source} observation={observation} />
        </section>
        <section className="surface map-surface" aria-labelledby="map-heading">
          <SurfaceHeading eyebrow="Geography" heading="Venue context" />
          <MapControls mode={mapMode} onModeChange={onMapModeChange} />
          <VenueMap mode={mapMode} source={source} />
        </section>
      </div>

      <section className="surface class-surface" aria-labelledby="classes-heading">
        <SurfaceHeading eyebrow="Detector output" heading="Vehicle classes" />
        {observation ? (
          <div className="class-grid">
            <ClassCount label="Cars" value={observation.class_counts.car} />
            <ClassCount label="Trucks" value={observation.class_counts.truck} />
            <ClassCount label="Buses" value={observation.class_counts.bus} />
            <ClassCount label="Motorcycles" value={observation.class_counts.motorcycle} />
          </div>
        ) : (
          <EmptyObservation />
        )}
      </section>
    </>
  );
}

function CameraView({ source }: { source: ReferenceSource | null }) {
  return (
    <section className="surface camera-view" aria-labelledby="camera-source-heading">
      <SurfaceHeading eyebrow="Selected source" heading="Public HLS stream" />
      <ReferenceVideoPlayer source={source} />
      <SourceMeta source={source} observation={null} />
      {source ? (
        <a className="source-link" href={source.video_url} rel="noreferrer" target="_blank">
          Open source stream <ExternalLink size={15} />
        </a>
      ) : null}
    </section>
  );
}

function MapView({ source, mode, onModeChange }: { source: ReferenceSource | null; mode: MapMode; onModeChange: (mode: MapMode) => void }) {
  return (
    <section className="surface full-map-surface" aria-labelledby="geographic-map-heading">
      <SurfaceHeading eyebrow="Geography" heading="Venue and reference locations" />
      <MapControls mode={mode} onModeChange={onModeChange} />
      <VenueMap mode={mode} source={source} />
    </section>
  );
}

function AuditView({ history }: { history: ReferenceObservation[] }) {
  return (
    <section className="surface audit-surface" aria-labelledby="audit-heading">
      <SurfaceHeading eyebrow="Ingress history" heading="Recent samples" />
      {history.length === 0 ? <EmptyObservation /> : null}
      {history.length > 0 ? (
        <div className="audit-table" role="table" aria-label="Recent reference samples">
          <div className="audit-row audit-heading-row" role="row"><span>Captured</span><span>Vehicles</span><span>Flow</span><span>Confidence</span><span>Latency</span></div>
          {history.map((sample) => (
            <div className="audit-row" key={`${sample.captured_at}-${sample.inference_ms}`} role="row">
              <span>{formatTimestamp(sample.captured_at)}</span>
              <span>{totalVehicles(sample.class_counts)}</span>
              <span>{formatFlow(sample.flow_delta_60s)}</span>
              <span>{Math.round(sample.confidence * 100)}%</span>
              <span>{sample.inference_ms} ms</span>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function MapControls({ mode, onModeChange }: { mode: MapMode; onModeChange: (mode: MapMode) => void }) {
  return (
    <div className="map-controls" aria-label="Map mode">
      <button className={mode === "venue" ? "is-selected" : undefined} onClick={() => onModeChange("venue")} type="button">Venue plan</button>
      <button className={mode === "reference" ? "is-selected" : undefined} onClick={() => onModeChange("reference")} type="button">Reference camera location</button>
    </div>
  );
}

function SourceMeta({ source, observation }: { source: ReferenceSource | null; observation: ReferenceObservation | null }) {
  if (!source) return <EmptyObservation />;
  return (
    <div className="source-meta">
      <span><MapPinned size={15} /> {source.name}</span>
      <span>{observation ? `Captured ${formatTimestamp(observation.captured_at)}` : source.attribution}</span>
    </div>
  );
}

function EmptyObservation() {
  return <p className="empty-observation">No reference observation received yet.</p>;
}

function SurfaceHeading({ eyebrow, heading }: { eyebrow: string; heading: string }) {
  return <div className="surface-heading"><p className="eyebrow">{eyebrow}</p><h2>{heading}</h2></div>;
}

function Metric({ icon, label, value, detail }: { icon: React.ReactNode; label: string; value: string; detail: string }) {
  return <section className="metric"><div className="metric-icon">{icon}</div><div><p>{label}</p><strong>{value}</strong><span>{detail}</span></div></section>;
}

function ClassCount({ label, value }: { label: string; value: number }) {
  return <div className="class-count"><span>{label}</span><strong>{value}</strong></div>;
}
