"use client";

import {
  Activity,
  ArrowUpRight,
  BellRing,
  Camera,
  CheckCircle2,
  ChevronRight,
  CircleAlert,
  Clock3,
  Eye,
  MapPinned,
  Radio,
  Route,
  Send,
  ShieldCheck,
  UsersRound,
} from "lucide-react";
import { useMemo, useState } from "react";
import { demoFeed, queueZones, type RiskLevel } from "@/lib/event-data";

const riskLabel: Record<RiskLevel, string> = {
  normal: "Stable",
  watch: "Watch",
  critical: "Critical",
};

export default function Home() {
  const [approved, setApproved] = useState(false);
  const [assigned, setAssigned] = useState(false);
  const [activeTab, setActiveTab] = useState("Live board");
  const criticalZone = queueZones[0];
  const recovery = approved ? 12 : 0;
  const activeZones = useMemo(
    () => queueZones.filter((zone) => zone.risk !== "normal").length,
    [],
  );

  function approveAction() {
    setApproved(true);
    setAssigned(true);
  }

  return (
    <main className="app-shell">
      <aside className="rail" aria-label="GridFlow navigation">
        <div className="brand-block">
          <div className="brand-mark" aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
          <div>
            <p className="eyebrow">Race-day operations</p>
            <h1>GRIDFLOW</h1>
          </div>
        </div>

        <nav className="primary-nav">
          {["Live board", "Cameras", "Runbooks", "Audit"].map((item, index) => {
            const Icon = [Activity, Camera, ShieldCheck, Clock3][index];
            return (
              <button
                className={activeTab === item ? "nav-item active" : "nav-item"}
                key={item}
                onClick={() => setActiveTab(item)}
                type="button"
              >
                <Icon size={17} strokeWidth={1.8} />
                <span>{item}</span>
              </button>
            );
          })}
        </nav>

        <div className="rail-footer">
          <div className="live-indicator"><span /> Live event</div>
          <p>Sunset Grand Prix<br />Egress window</p>
          <strong>18:42 IST</strong>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Event control / Session 04</p>
            <div className="heading-line">
              <h2>Race-end egress</h2>
              <span className="session-chip"><Radio size={13} /> Live</span>
            </div>
          </div>
          <div className="top-actions">
            <button className="icon-button" type="button" aria-label="Open event map" title="Open event map">
              <MapPinned size={18} />
            </button>
            <button className="icon-button notification" type="button" aria-label="View notifications" title="View notifications">
              <BellRing size={18} />
              <span />
            </button>
            <div className="operator"><span>AK</span><div><strong>A. Kapoor</strong><small>Event controller</small></div></div>
          </div>
        </header>

        <div className="incident-strip">
          <div className="incident-leading"><CircleAlert size={20} /><span>1 critical queue needs a decision</span></div>
          <span>Source confidence 91%</span>
          <button type="button" onClick={() => document.getElementById("decision")?.scrollIntoView({ behavior: "smooth" })}>Review now <ChevronRight size={16} /></button>
        </div>

        <section className="metric-row" aria-label="Event summary">
          <Metric icon={<UsersRound size={18} />} label="Observed guests" value="1,020" detail="Across 4 active zones" tone="light" />
          <Metric icon={<Activity size={18} />} label="Zones needing attention" value={String(activeZones)} detail="1 critical, 1 watch" tone="amber" />
          <Metric icon={<Camera size={18} />} label="Camera health" value="4 / 4" detail="All feeds fresh" tone="green" />
          <Metric icon={<Route size={18} />} label="Recovery after action" value={approved ? `${recovery}%` : "--"} detail={approved ? "South Exit improving" : "Awaiting approval"} tone="cyan" />
        </section>

        <div className="board-grid">
          <section className="zone-panel" aria-labelledby="zone-heading">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Live occupancy</p>
                <h3 id="zone-heading">Venue queue map</h3>
              </div>
              <button className="text-button" type="button">Full map <ArrowUpRight size={15} /></button>
            </div>

            <div className="venue-map" role="img" aria-label="Simplified queue risk map of the Grand Prix venue">
              <div className="track-loop" />
              <div className="grandstand g-one">G1</div>
              <div className="grandstand g-two">G2</div>
              <div className="grandstand g-three">G3</div>
              <div className="route-line route-blue" />
              <div className="route-line route-red" />
              {queueZones.map((zone) => (
                <button key={zone.id} type="button" className={`map-node ${zone.id} ${zone.risk}`} title={`${zone.name}: ${riskLabel[zone.risk]}`}>
                  <span className="node-core" />
                  <span>{zone.name}</span>
                </button>
              ))}
              <div className="map-key"><span className="key-critical" /> Critical <span className="key-watch" /> Watch <span className="key-normal" /> Stable</div>
            </div>
          </section>

          <section className="risk-panel" id="decision" aria-labelledby="risk-heading">
            <div className="panel-heading">
              <div>
                <p className="eyebrow red">Priority alert</p>
                <h3 id="risk-heading">{criticalZone.name}</h3>
              </div>
              <span className="status-critical">Critical</span>
            </div>
            <div className="risk-numbers">
              <div><span>Occupancy</span><strong>{criticalZone.occupancy}<small> / {criticalZone.capacity}</small></strong></div>
              <div><span>Queue growth</span><strong>+{criticalZone.trend}<small>% / 5 min</small></strong></div>
            </div>
            <div className="occupancy-scale"><span style={{ width: `${(criticalZone.occupancy / criticalZone.capacity) * 100}%` }} /></div>
            <div className="evidence-row"><Eye size={17} /><span>Detector and density estimates agree within 7%</span><strong>91%</strong></div>
            <p className="risk-copy">The south concourse is loading faster than the exit can clear. A queue spillback reaches the grandstand stairs in an estimated 6 minutes.</p>
            <div className="recommendation"><Route size={19} /><div><span>Recommended response</span><strong>Open Gate 5 and publish the Blue Route</strong></div></div>
            {!approved ? (
              <button className="approve-button" type="button" onClick={approveAction}><Send size={17} /> Approve and publish</button>
            ) : (
              <div className="approved-state"><CheckCircle2 size={18} /> Response sent to Gate 5 signage and steward channel</div>
            )}
          </section>
        </div>

        <div className="lower-grid">
          <section className="feed-panel" aria-labelledby="feed-heading">
            <div className="panel-heading">
              <div><p className="eyebrow">Evidence frame</p><h3 id="feed-heading">Cam 04 / South Exit</h3></div>
              <span className="camera-live"><span /> {criticalZone.freshness}</span>
            </div>
            <div className="feed-image">
              {/* Pexels footage still, used with source attribution in the README. */}
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={demoFeed} alt="Crowd queue observation from the demo camera feed" />
              <span className="detector-box box-one" /><span className="detector-box box-two" /><span className="detector-box box-three" /><span className="detector-box box-four" />
              <div className="feed-label"><Camera size={14} /> Person detector + density pass</div>
            </div>
            <div className="feed-caption"><span><span className="signal-dot" /> Privacy-filtered queue zone</span><a href="https://www.pexels.com/video/queue-of-people-in-urban-setting-during-daytime-35253208/" target="_blank" rel="noreferrer">Demo media source <ArrowUpRight size={13} /></a></div>
          </section>

          <section className="runbook-panel" aria-labelledby="runbook-heading">
            <div className="panel-heading"><div><p className="eyebrow">Human response</p><h3 id="runbook-heading">Runbook 03 / Relief exit</h3></div><ShieldCheck size={20} /></div>
            <ol className="runbook-list">
              <li className="done"><span>1</span><div><strong>Verify camera evidence</strong><small>Completed by A. Kapoor</small></div><CheckCircle2 size={18} /></li>
              <li className={assigned ? "done" : "current"}><span>2</span><div><strong>Deploy Gate 5 steward</strong><small>{assigned ? "Assigned to S. Mehta" : "Assign a steward on channel B"}</small></div>{assigned ? <CheckCircle2 size={18} /> : <button type="button" onClick={() => setAssigned(true)}>Assign</button>}</li>
              <li className={approved ? "current" : "future"}><span>3</span><div><strong>Update exit signage</strong><small>{approved ? "Blue Route published" : "Requires supervisor approval"}</small></div>{approved ? <CheckCircle2 size={18} /> : <Clock3 size={18} />}</li>
            </ol>
            <a className="signage-link" href="/display" target="_blank" rel="noreferrer">Open live signage view <ArrowUpRight size={15} /></a>
          </section>
        </div>
      </section>
    </main>
  );
}

function Metric({ icon, label, value, detail, tone }: { icon: React.ReactNode; label: string; value: string; detail: string; tone: string }) {
  return <section className={`metric ${tone}`}><div className="metric-icon">{icon}</div><div><p>{label}</p><strong>{value}</strong><small>{detail}</small></div></section>;
}
