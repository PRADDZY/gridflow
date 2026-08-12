export type RiskLevel = "normal" | "watch" | "critical";

export type QueueZone = {
  id: string;
  name: string;
  area: string;
  occupancy: number;
  capacity: number;
  trend: number;
  risk: RiskLevel;
  camera: string;
  freshness: string;
};

export const queueZones: QueueZone[] = [
  {
    id: "south-exit",
    name: "South Exit",
    area: "Grandstand C egress",
    occupancy: 432,
    capacity: 520,
    trend: 18,
    risk: "critical",
    camera: "Cam 04",
    freshness: "6 sec ago",
  },
  {
    id: "north-concourse",
    name: "North Concourse",
    area: "Fan zone crossing",
    occupancy: 268,
    capacity: 540,
    trend: 6,
    risk: "watch",
    camera: "Cam 11",
    freshness: "4 sec ago",
  },
  {
    id: "shuttle-hub",
    name: "Shuttle Hub",
    area: "Blue route queue",
    occupancy: 146,
    capacity: 360,
    trend: -4,
    risk: "normal",
    camera: "Cam 08",
    freshness: "8 sec ago",
  },
  {
    id: "west-gate",
    name: "West Gate",
    area: "Pedestrian exit",
    occupancy: 174,
    capacity: 420,
    trend: 2,
    risk: "normal",
    camera: "Cam 02",
    freshness: "10 sec ago",
  },
];

export const demoFeed =
  "https://images.pexels.com/videos/35253208/2025-35253208.jpeg?auto=compress&dpr=1&h=750&w=1260";

export const signageCopy = {
  route: "BLUE ROUTE",
  headline: "SOUTH EXIT BUSY",
  message: "Use Gate 5 for the fastest exit.",
};
