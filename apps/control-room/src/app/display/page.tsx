"use client";

import { ArrowRight, Route, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { type SignagePayload } from "@/lib/signage";

export default function DisplayPage() {
  const [signage, setSignage] = useState<SignagePayload>({ state: "pending" });
  const publishedSignage = signage.state === "published" ? signage : null;
  const published = publishedSignage !== null;

  useEffect(() => {
    let active = true;

    async function refreshSignage() {
      try {
        const response = await fetch("/api/signage", { cache: "no-store" });
        if (!response.ok) return;
        const payload = (await response.json()) as SignagePayload;
        if (active) setSignage(payload);
      } catch {
        // A display without verified state must stay on the safe default message.
      }
    }

    void refreshSignage();
    const interval = window.setInterval(refreshSignage, 5_000);
    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  return (
    <main className={published ? "display-shell published" : "display-shell pending"}>
      <div className="display-top"><span>GRIDFLOW WAYFINDING</span><span><ShieldCheck size={18} /> {published ? "Verified operator message" : "No active route"}</span></div>
      <section className="display-content">
        <p>{publishedSignage ? publishedSignage.route : "PLEASE FOLLOW STEWARD DIRECTIONS"}</p>
        <h1>{publishedSignage ? publishedSignage.headline : "AWAITING APPROVAL"}</h1>
        <h2>{publishedSignage ? publishedSignage.message : "A verified route will appear here after controller approval."}</h2>
        {publishedSignage ? (
          <div className="display-route"><Route size={44} /><ArrowRight size={74} /><strong>{publishedSignage.destination}</strong></div>
        ) : (
          <div className="display-route"><ShieldCheck size={44} /><strong>STEWARDS ON SITE</strong></div>
        )}
      </section>
      <footer>{published ? "Follow steward directions. Do not stop at the concourse entrance." : "Follow steward directions. Do not enter a closed route."}</footer>
    </main>
  );
}
