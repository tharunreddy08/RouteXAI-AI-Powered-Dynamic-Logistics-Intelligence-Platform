import { useEffect, useState } from "react";
import { History } from "lucide-react";
import { routeHistoryApi } from "../lib/api";
import type { RouteHistoryEntry } from "../lib/types";
import { TrafficBadge } from "../components/Badges";

export default function RouteHistoryPage() {
  const [rows, setRows] = useState<RouteHistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    routeHistoryApi
      .list(100)
      .then(setRows)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-display text-xl text-ink flex items-center gap-2">
          <History size={18} className="text-signal" /> Route History
        </h1>
        <p className="text-sm text-ink-faint mt-1">
          Predicted vs. actual ETA per delivery — this is what feeds the self-learning ETA model.
        </p>
      </div>

      <div className="panel overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-ink-faint border-b border-panelBorder bg-base-800/40">
              <th className="px-4 py-2.5 font-normal">Vehicle</th>
              <th className="px-4 py-2.5 font-normal">Distance</th>
              <th className="px-4 py-2.5 font-normal">Predicted ETA</th>
              <th className="px-4 py-2.5 font-normal">Actual ETA</th>
              <th className="px-4 py-2.5 font-normal">Delay</th>
              <th className="px-4 py-2.5 font-normal">Traffic</th>
              <th className="px-4 py-2.5 font-normal">CO2</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-b border-panelBorder/40 last:border-0">
                <td className="px-4 py-2.5 font-mono text-xs text-ink">#{r.vehicle_id}</td>
                <td className="px-4 py-2.5 text-ink-dim font-mono text-xs">{r.distance.toFixed(1)} km</td>
                <td className="px-4 py-2.5 text-ink-dim font-mono text-xs">
                  {r.eta_predicted ? `${r.eta_predicted.toFixed(0)} min` : "—"}
                </td>
                <td className="px-4 py-2.5 text-ink-dim font-mono text-xs">
                  {r.eta_actual ? `${r.eta_actual.toFixed(0)} min` : "—"}
                </td>
                <td className={`px-4 py-2.5 font-mono text-xs ${r.delay > 10 ? "text-status-danger" : "text-ink-dim"}`}>
                  {r.delay.toFixed(0)} min
                </td>
                <td className="px-4 py-2.5">
                  <TrafficBadge mode={r.traffic_mode} />
                </td>
                <td className="px-4 py-2.5 text-ink-dim font-mono text-xs">{r.co2_emissions.toFixed(1)} kg</td>
              </tr>
            ))}
            {rows.length === 0 && !loading && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-ink-faint text-sm">
                  No route history recorded yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
