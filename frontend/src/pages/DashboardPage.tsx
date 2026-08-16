import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Package, Truck, Gauge, Leaf, Radio, Cpu } from "lucide-react";
import { ordersApi, fleetApi, hardwareApi, mlApi } from "../lib/api";
import type { Order, Vehicle, FleetStatus, HardwareEvent, MLStatus } from "../lib/types";
import { VehicleStatusBadge, OrderStatusBadge } from "../components/Badges";
import { useAuth } from "../lib/auth";

const ACCENT_STYLES: Record<string, string> = {
  signal: "bg-signal/10 text-signal",
  "route-4": "bg-route-4/10 text-route-4",
  "status-success": "bg-status-success/10 text-status-success",
  "status-warn": "bg-status-warn/10 text-status-warn",
};

function KpiCard({
  icon,
  label,
  value,
  sub,
  accent = "signal",
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub?: string;
  accent?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="panel p-4"
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-ink-faint uppercase tracking-wide">{label}</span>
        <div className={`w-7 h-7 rounded-md flex items-center justify-center ${ACCENT_STYLES[accent]}`}>
          {icon}
        </div>
      </div>
      <div className="font-display text-2xl text-ink">{value}</div>
      {sub && <div className="text-xs text-ink-faint mt-1">{sub}</div>}
    </motion.div>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [orders, setOrders] = useState<Order[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [status, setStatus] = useState<FleetStatus | null>(null);
  const [events, setEvents] = useState<HardwareEvent[]>([]);
  const [ml, setMl] = useState<MLStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      ordersApi.list(),
      fleetApi.vehicles(),
      fleetApi.status(),
      hardwareApi.events(),
      mlApi.status(),
    ])
      .then(([o, v, s, e, m]) => {
        setOrders(o);
        setVehicles(v);
        setStatus(s);
        setEvents(e.slice(0, 5));
        setMl(m);
      })
      .finally(() => setLoading(false));
  }, []);

  const onTime = orders.length
    ? Math.round((orders.filter((o) => o.status === "Completed").length / orders.length) * 100)
    : 0;

  if (loading) {
    return <div className="text-ink-faint text-sm font-mono">Loading command center…</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-xl text-ink">
          Welcome back, {user?.name?.split(" ")[0]}
        </h1>
        <p className="text-sm text-ink-faint mt-1">
          Fleet-wide overview across {vehicles.length} vehicles and {orders.length} orders.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard icon={<Package size={15} />} label="Total Orders" value={String(orders.length)} accent="signal" />
        <KpiCard
          icon={<Truck size={15} />}
          label="Active Vans"
          value={`${status?.active_vehicles ?? 0}/${status?.total_vehicles ?? 0}`}
          accent="route-4"
        />
        <KpiCard icon={<Gauge size={15} />} label="On-Time Delivery" value={`${onTime}%`} accent="status-success" />
        <KpiCard
          icon={<Leaf size={15} />}
          label="Fleet CO2"
          value={`${status?.total_co2_emissions?.toFixed(1) ?? 0} kg`}
          sub={`${status?.total_fuel_used?.toFixed(1) ?? 0} L fuel used`}
          accent="status-warn"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Fleet snapshot */}
        <div className="lg:col-span-2 panel p-4">
          <h2 className="font-display text-sm text-ink mb-3">Fleet Snapshot</h2>
          <div className="space-y-2">
            {vehicles.map((v) => (
              <div
                key={v.id}
                className="flex items-center justify-between px-3 py-2 rounded-lg bg-base-800/60 border border-panelBorder/60"
              >
                <div className="flex items-center gap-3">
                  <span className="font-mono text-sm text-ink">{v.name}</span>
                  <span className="text-xs text-ink-faint">{v.driver_name}</span>
                </div>
                <div className="flex items-center gap-4 text-xs text-ink-faint font-mono">
                  <span>{v.current_eta || "—"}</span>
                  <span>{v.fuel_consumption.toFixed(1)}L</span>
                  <VehicleStatusBadge status={v.status} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent orders + ML status */}
        <div className="space-y-4">
          <div className="panel p-4">
            <h2 className="font-display text-sm text-ink mb-3 flex items-center gap-2">
              <Radio size={14} className="text-signal" /> Recent Hardware Events
            </h2>
            {events.length === 0 ? (
              <p className="text-xs text-ink-faint">No events yet.</p>
            ) : (
              <div className="space-y-2">
                {events.map((e) => (
                  <div key={e.id} className="text-xs flex items-center justify-between">
                    <span className={e.event_type === "BLOCK_DETECTED" ? "text-status-danger" : "text-status-success"}>
                      {e.event_type.replace("_", " ")}
                    </span>
                    <span className="text-ink-faint font-mono">Vehicle #{e.vehicle_id}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="panel p-4">
            <h2 className="font-display text-sm text-ink mb-3 flex items-center gap-2">
              <Cpu size={14} className="text-signal" /> ML Insights
            </h2>
            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between">
                <span className="text-ink-faint">Model</span>
                <span className="text-ink-dim">{ml?.eta_prediction_model}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-ink-faint">Optimizer</span>
                <span className="text-ink-dim">{ml?.optimization_engine}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-ink-faint">Shortest Path</span>
                <span className="text-ink-dim">{ml?.shortest_path_algorithm}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-ink-faint">Trained</span>
                <span className={ml?.model_trained ? "text-status-success" : "text-status-warn"}>
                  {ml?.model_trained ? "Yes" : "Not yet (heuristic fallback)"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-ink-faint">Samples</span>
                <span className="text-ink-dim">
                  {ml?.training_samples_available}/{ml?.min_samples_required} min
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="panel p-4">
        <h2 className="font-display text-sm text-ink mb-3">Recent Orders</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-ink-faint border-b border-panelBorder">
                <th className="pb-2 font-normal">Customer</th>
                <th className="pb-2 font-normal">Address</th>
                <th className="pb-2 font-normal">Status</th>
                <th className="pb-2 font-normal">Priority</th>
              </tr>
            </thead>
            <tbody>
              {orders.slice(0, 6).map((o) => (
                <tr key={o.id} className="border-b border-panelBorder/40 last:border-0">
                  <td className="py-2 text-ink">{o.customer_name}</td>
                  <td className="py-2 text-ink-faint">{o.address}</td>
                  <td className="py-2">
                    <OrderStatusBadge status={o.status} />
                  </td>
                  <td className="py-2 text-ink-dim">{o.priority}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
