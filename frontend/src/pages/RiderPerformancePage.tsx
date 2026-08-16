import { useEffect, useState } from "react";
import { Users, Trophy } from "lucide-react";
import { ridersApi } from "../lib/api";
import type { RiderPerformance } from "../lib/types";

export default function RiderPerformancePage() {
  const [rows, setRows] = useState<RiderPerformance[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    ridersApi
      .performance()
      .then(setRows)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-display text-xl text-ink flex items-center gap-2">
          <Users size={18} className="text-signal" /> Rider Performance
        </h1>
        <p className="text-sm text-ink-faint mt-1">Ranked by efficiency score.</p>
      </div>

      <div className="panel overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-ink-faint border-b border-panelBorder bg-base-800/40">
              <th className="px-4 py-2.5 font-normal">Rank</th>
              <th className="px-4 py-2.5 font-normal">Rider</th>
              <th className="px-4 py-2.5 font-normal">Deliveries</th>
              <th className="px-4 py-2.5 font-normal">On-Time %</th>
              <th className="px-4 py-2.5 font-normal">Avg Delay</th>
              <th className="px-4 py-2.5 font-normal">Route Adherence</th>
              <th className="px-4 py-2.5 font-normal">Efficiency</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={r.rider_id} className="border-b border-panelBorder/40 last:border-0">
                <td className="px-4 py-2.5">
                  {i === 0 ? (
                    <span className="flex items-center gap-1 text-status-warn">
                      <Trophy size={13} /> 1
                    </span>
                  ) : (
                    <span className="text-ink-faint">{i + 1}</span>
                  )}
                </td>
                <td className="px-4 py-2.5 text-ink">{r.rider_name}</td>
                <td className="px-4 py-2.5 text-ink-dim font-mono text-xs">{r.deliveries_completed}</td>
                <td className="px-4 py-2.5 text-ink-dim font-mono text-xs">{r.on_time_percentage.toFixed(1)}%</td>
                <td className="px-4 py-2.5 text-ink-dim font-mono text-xs">{r.average_delay.toFixed(1)} min</td>
                <td className="px-4 py-2.5 text-ink-dim font-mono text-xs">{r.route_adherence.toFixed(1)}%</td>
                <td className="px-4 py-2.5 text-signal font-mono text-xs">{r.efficiency_score.toFixed(1)}</td>
              </tr>
            ))}
            {rows.length === 0 && !loading && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-ink-faint text-sm">
                  No rider performance data yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
