/**
 * Simulated analytics data for the Daily/Weekly/Monthly/Yearly views.
 *
 * Per spec section 22: "No backend calculations are required for these
 * analysis visualizations; simulated frontend data is acceptable." This
 * generator is deterministic (seeded by the selected date/range) so the
 * same filter always reproduces the same numbers rather than jumping
 * around on every re-render — closer to how a cached report would behave.
 *
 * This is explicitly separate from the real backend-driven data used
 * elsewhere in the app (orders, fleet, ML predictions, route history).
 */

export interface AnalyticsPoint {
  label: string; // "09:00", "Mon", "14", "2024"
  deliveries: number;
  avgEtaMinutes: number;
  fuelEfficiencyPct: number;
  delayPct: number;
}

export interface AnalyticsSummary {
  totalDeliveries: number;
  avgEtaMinutes: number;
  onTimePct: number;
  trafficImpactIndex: number; // 0-100, higher = traffic hurting performance more
}

// Simple deterministic PRNG (mulberry32) seeded from a string.
function seededRandom(seed: string) {
  let h = 1779033703 ^ seed.length;
  for (let i = 0; i < seed.length; i++) {
    h = Math.imul(h ^ seed.charCodeAt(i), 3432918353);
    h = (h << 13) | (h >>> 19);
  }
  return function () {
    h = Math.imul(h ^ (h >>> 16), 2246822507);
    h = Math.imul(h ^ (h >>> 13), 3266489909);
    h ^= h >>> 16;
    return (h >>> 0) / 4294967296;
  };
}

function genPoint(rand: () => number, label: string, baseDeliveries: number): AnalyticsPoint {
  const deliveries = Math.max(0, Math.round(baseDeliveries + (rand() - 0.5) * baseDeliveries * 0.6));
  const avgEtaMinutes = Math.round(22 + rand() * 26);
  const fuelEfficiencyPct = Math.round(72 + rand() * 22);
  const delayPct = Math.round(rand() * 22);
  return { label, deliveries, avgEtaMinutes, fuelEfficiencyPct, delayPct };
}

export function generateDaily(dateISO: string): AnalyticsPoint[] {
  const rand = seededRandom(`daily-${dateISO}`);
  const points: AnalyticsPoint[] = [];
  for (let h = 0; h < 24; h++) {
    const businessHour = h >= 8 && h <= 20;
    points.push(genPoint(rand, `${String(h).padStart(2, "0")}:00`, businessHour ? 14 : 3));
  }
  return points;
}

export function generateWeekly(startDateISO: string): AnalyticsPoint[] {
  const rand = seededRandom(`weekly-${startDateISO}`);
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  return days.map((d) => genPoint(rand, d, d === "Sat" || d === "Sun" ? 60 : 110));
}

export function generateMonthly(month: number, year: number): AnalyticsPoint[] {
  const rand = seededRandom(`monthly-${year}-${month}`);
  const daysInMonth = new Date(year, month, 0).getDate();
  const points: AnalyticsPoint[] = [];
  for (let d = 1; d <= daysInMonth; d++) {
    points.push(genPoint(rand, String(d), 95));
  }
  return points;
}

export function generateYearly(startYear = 2022, count = 5): AnalyticsPoint[] {
  const rand = seededRandom(`yearly-${startYear}-${count}`);
  const points: AnalyticsPoint[] = [];
  for (let i = 0; i < count; i++) {
    const year = startYear + i;
    points.push(genPoint(rand, String(year), 2800 + i * 350));
  }
  return points;
}

export function summarize(points: AnalyticsPoint[]): AnalyticsSummary {
  if (points.length === 0) {
    return { totalDeliveries: 0, avgEtaMinutes: 0, onTimePct: 0, trafficImpactIndex: 0 };
  }
  const totalDeliveries = points.reduce((s, p) => s + p.deliveries, 0);
  const avgEtaMinutes = Math.round(points.reduce((s, p) => s + p.avgEtaMinutes, 0) / points.length);
  const avgDelayPct = points.reduce((s, p) => s + p.delayPct, 0) / points.length;
  const onTimePct = Math.round(Math.max(0, 100 - avgDelayPct * 1.4));
  const trafficImpactIndex = Math.round(avgDelayPct * 3.2);
  return { totalDeliveries, avgEtaMinutes, onTimePct, trafficImpactIndex };
}
