import type { OrderPriority, OrderStatus, VehicleStatus, TrafficMode } from "../lib/types";

export function PriorityBadge({ priority }: { priority: OrderPriority }) {
  const styles: Record<OrderPriority, string> = {
    Normal: "bg-base-700 text-ink-dim",
    Express: "bg-status-express/15 text-status-express border border-status-express/30",
    Emergency: "bg-status-emergency/15 text-status-emergency border border-status-emergency/30",
  };
  return <span className={`badge ${styles[priority]}`}>{priority}</span>;
}

export function OrderStatusBadge({ status }: { status: OrderStatus }) {
  const styles: Record<OrderStatus, string> = {
    Unassigned: "bg-base-700 text-ink-dim",
    Assigned: "bg-signal/15 text-signal border border-signal/30",
    "In Progress": "bg-route-4/15 text-route-4 border border-route-4/30",
    Completed: "bg-status-success/15 text-status-success border border-status-success/30",
    Delayed: "bg-status-warn/15 text-status-warn border border-status-warn/30",
    Cancelled: "bg-status-danger/15 text-status-danger border border-status-danger/30",
  };
  return <span className={`badge ${styles[status]}`}>{status}</span>;
}

export function VehicleStatusBadge({ status }: { status: VehicleStatus }) {
  const styles: Record<VehicleStatus, string> = {
    Idle: "bg-base-700 text-ink-dim",
    Active: "bg-status-success/15 text-status-success border border-status-success/30",
    Blocked: "bg-status-danger/15 text-status-danger border border-status-danger/30",
    Offline: "bg-base-700 text-ink-faint",
  };
  return (
    <span className={`badge ${styles[status]}`}>
      {status === "Active" && (
        <span className="w-1.5 h-1.5 rounded-full bg-status-success animate-pulseDot" />
      )}
      {status}
    </span>
  );
}

export function TrafficBadge({ mode }: { mode: TrafficMode }) {
  const styles: Record<TrafficMode, string> = {
    Normal: "bg-status-success/15 text-status-success border border-status-success/30",
    Heavy: "bg-status-warn/15 text-status-warn border border-status-warn/30",
    Accident: "bg-status-danger/15 text-status-danger border border-status-danger/30",
  };
  return <span className={`badge ${styles[mode]}`}>{mode} Traffic</span>;
}
