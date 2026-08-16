import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { UploadCloud, PlusSquare, RefreshCw, Sparkles } from "lucide-react";
import { ordersApi, routesApi, extractError } from "../lib/api";
import type { Order, OrderStatus } from "../lib/types";
import { OrderStatusBadge, PriorityBadge } from "../components/Badges";
import { useToast } from "../lib/toast";

const STATUS_FILTERS: (OrderStatus | "All")[] = [
  "All",
  "Unassigned",
  "Assigned",
  "In Progress",
  "Completed",
  "Delayed",
  "Cancelled",
];

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<OrderStatus | "All">("All");
  const [uploading, setUploading] = useState(false);
  const [optimizing, setOptimizing] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);
  const { push } = useToast();

  function load() {
    setLoading(true);
    ordersApi
      .list()
      .then(setOrders)
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const result = await ordersApi.upload(file);
      push(
        result.failed > 0 ? "info" : "success",
        `Uploaded ${result.created} orders${result.failed ? `, ${result.failed} rows failed` : ""}.`
      );
      load();
    } catch (err) {
      push("error", extractError(err).message);
    } finally {
      setUploading(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  }

  async function handleOptimizeAll() {
    setOptimizing(true);
    try {
      const result = await routesApi.optimize(undefined, "Normal");
      push(
        "success",
        `Optimized: ${result.routes_created} routes, ${result.orders_assigned} orders assigned across ${result.vehicles_used} vehicles.`
      );
      load();
    } catch (err) {
      push("error", extractError(err).message);
    } finally {
      setOptimizing(false);
    }
  }

  const filtered = filter === "All" ? orders : orders.filter((o) => o.status === filter);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-display text-xl text-ink">Orders</h1>
          <p className="text-sm text-ink-faint mt-1">{orders.length} total orders</p>
        </div>
        <div className="flex items-center gap-2">
          <input ref={fileInput} type="file" accept=".csv,.json" className="hidden" onChange={handleFile} />
          <button
            onClick={() => fileInput.current?.click()}
            disabled={uploading}
            className="flex items-center gap-1.5 text-sm px-3 py-2 rounded-lg border border-panelBorder text-ink-dim hover:text-ink hover:border-signal/40 transition-colors disabled:opacity-60"
          >
            <UploadCloud size={15} /> {uploading ? "Uploading…" : "Upload CSV/JSON"}
          </button>
          <button
            onClick={handleOptimizeAll}
            disabled={optimizing}
            className="flex items-center gap-1.5 text-sm px-3 py-2 rounded-lg bg-signal/15 border border-signal/40 text-signal hover:bg-signal/25 transition-colors disabled:opacity-60"
          >
            <Sparkles size={15} /> {optimizing ? "Optimizing…" : "Optimize All"}
          </button>
          <Link
            to="/orders/new"
            className="flex items-center gap-1.5 text-sm px-3 py-2 rounded-lg bg-signal text-base-950 font-medium hover:bg-signal-glow transition-colors"
          >
            <PlusSquare size={15} /> New Order
          </Link>
          <button
            onClick={load}
            className="p-2 rounded-lg border border-panelBorder text-ink-faint hover:text-ink transition-colors"
            title="Refresh"
          >
            <RefreshCw size={15} className={loading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5">
        {STATUS_FILTERS.map((s) => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
              filter === s
                ? "bg-signal/15 border-signal/40 text-signal"
                : "border-panelBorder text-ink-faint hover:text-ink"
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      <div className="panel overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-ink-faint border-b border-panelBorder bg-base-800/40">
                <th className="px-4 py-2.5 font-normal">Customer</th>
                <th className="px-4 py-2.5 font-normal">Address</th>
                <th className="px-4 py-2.5 font-normal">Priority</th>
                <th className="px-4 py-2.5 font-normal">Status</th>
                <th className="px-4 py-2.5 font-normal">Weight</th>
                <th className="px-4 py-2.5 font-normal">Source</th>
                <th className="px-4 py-2.5 font-normal">Vehicle</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((o) => (
                <tr key={o.id} className="border-b border-panelBorder/40 last:border-0 hover:bg-base-800/30">
                  <td className="px-4 py-2.5 text-ink">{o.customer_name}</td>
                  <td className="px-4 py-2.5 text-ink-faint max-w-xs truncate">{o.address}</td>
                  <td className="px-4 py-2.5">
                    <PriorityBadge priority={o.priority} />
                  </td>
                  <td className="px-4 py-2.5">
                    <OrderStatusBadge status={o.status} />
                  </td>
                  <td className="px-4 py-2.5 text-ink-dim font-mono text-xs">{o.package_weight} kg</td>
                  <td className="px-4 py-2.5 text-ink-faint text-xs">{o.created_via}</td>
                  <td className="px-4 py-2.5 text-ink-faint text-xs font-mono">
                    {o.assigned_vehicle_id ? `#${o.assigned_vehicle_id}` : "—"}
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && !loading && (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-ink-faint text-sm">
                    No orders match this filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
