import { ArrowRight, Route, ShieldCheck } from "lucide-react";
import { signageCopy } from "@/lib/event-data";

export default function DisplayPage() {
  return (
    <main className="display-shell">
      <div className="display-top"><span>GRIDFLOW WAYFINDING</span><span><ShieldCheck size={18} /> Verified operator message</span></div>
      <section className="display-content">
        <p>{signageCopy.route}</p>
        <h1>{signageCopy.headline}</h1>
        <h2>{signageCopy.message}</h2>
        <div className="display-route"><Route size={44} /><ArrowRight size={74} /><strong>GATE 5</strong></div>
      </section>
      <footer>Follow steward directions. Do not stop at the concourse entrance.</footer>
    </main>
  );
}
