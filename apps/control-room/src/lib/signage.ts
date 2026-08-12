import { hasPublishedSignAction, type EventSnapshot } from "@/lib/live-state";

export type SignagePayload =
  | {
      state: "pending";
    }
  | {
      state: "published";
      route: string;
      headline: string;
      message: string;
      destination: string;
    };

const BLUE_ROUTE_ACTION = "Publish Blue Route diversion to approved displays.";

export function signageForSnapshot(snapshot: EventSnapshot): SignagePayload {
  if (!hasPublishedSignAction(snapshot) || snapshot.recommendation.sign_action !== BLUE_ROUTE_ACTION) {
    return { state: "pending" };
  }
  return {
    state: "published",
    route: "BLUE ROUTE",
    headline: "SOUTH EXIT BUSY",
    message: "Use Gate 5 for the fastest exit.",
    destination: "GATE 5",
  };
}
