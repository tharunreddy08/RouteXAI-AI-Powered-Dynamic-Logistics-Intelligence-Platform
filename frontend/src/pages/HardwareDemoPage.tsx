import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Radio, AlertTriangle, CheckCircle2, Zap } from "lucide-react";
import { fleetApi, hardwareApi, extractError } from "../lib/api";
import type { Vehicle, HardwareEvent } from "../lib/types";
import { VehicleStatusBadge } from "../components/Badges";
import { useToast } from "../lib/toast";

export default function HardwareDemoPage() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [events, setEvents] = useState<HardwareEvent[]>([]);
  const [busyVehicle, setBusyVehicle] = useState<number | null>(null);
  const [signalActive, setSignalActive] = useState<number | null>(null);
  const { push } = useToast();

  function load() {
    Promise.all([fleetApi.vehicles(), hardwareApi.events()]).then(([v, e]) => {
      setVehicles(v);
      setEvents(e);
      const openBlock = e.find((ev) => ev.event_type === "BLOCK_DETECTED" && ev.status === "Active");
      setSignalActive(openBlock ? openBlock.vehicle_id : null);
    });
  }

  useEffect(load, []);

  async function handleBlock(vehicleId: number) {
    setBusyVehicle(vehicleId);
    try {
      const result = await hardwareApi.block(vehicleId);
      if (result.rerouted) {
        push(
          "success",
          `Vehicle #${vehicleId} rerouted: +${result.detour_distance_km?.toFixed(2)} km detour, new ETA ${result.new_eta}.`
        );
      } else {
        push("info", `Block logged for vehicle #${vehicleId} (${result.reason}).`);
      }
      load();
    } catch (err) {
      push("error", extractError(err).message);
    } finally {
      setBusyVehicle(null);
    }
  }

  async function handleClear(vehicleId: number) {
    setBusyVehicle(vehicleId);
    try {
      const result = await hardwareApi.clear(vehicleId);
      push("success", `Block cleared on vehicle #${vehicleId}.${result.route_recalculated ? " Route recalculated." : ""}`);
      load();
    } catch (err) {
      push("error", extractError(err).message);
    } finally {
      setBusyVehicle(null);
    }
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-display text-xl text-ink flex items-center gap-2">
          <Radio size={18} className="text-signal" /> Hardware Demo
        </h1>
        <p className="text-sm text-ink-faint mt-1">
          Simulates an ultrasonic sensor signal. Only the affected vehicle reroutes — every other
          vehicle continues on its existing route.
        </p>
      </div>

      <AnimatePresence>
        {signalActive && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="flex items-center gap-2 bg-status-danger/10 border border-status-danger/30 rounded-lg px-4 py-2.5 text-sm text-status-danger"
          >
            <Zap size={15} className="animate-pulseDot" />
            Hardware Signal Active — Vehicle #{signalActive} obstruction reported
          </motion.div>
        )}
      </AnimatePresence>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {vehicles.map((v) => (
          <div key={v.id} className="panel p-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <span className="font-mono text-sm text-ink">{v.name}</span>
                <span className="text-xs text-ink-faint ml-2">{v.driver_name}</span>
              </div>
              <VehicleStatusBadge status={v.status} />
            </div>
            <div className="text-xs text-ink-faint mb-3 space-y-0.5">
              <div>Current ETA: {v.current_eta || "—"}</div>
              <div>Fuel: {v.fuel_consumption.toFixed(1)} L · CO2: {v.co2_emissions.toFixed(1)} kg</div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handleBlock(v.id)}
                disabled={busyVehicle === v.id}
                className="flex-1 flex items-center justify-center gap-1.5 text-xs px-3 py-2 rounded-lg bg-status-danger/15 border border-status-danger/40 text-status-danger hover:bg-status-danger/25 transition-colors disabled:opacity-60"
              >
                <AlertTriangle size={13} /> Trigger BLOCK_DETECTED
              </button>
              <button
                onClick={() => handleClear(v.id)}
                disabled={busyVehicle === v.id}
                className="flex-1 flex items-center justify-center gap-1.5 text-xs px-3 py-2 rounded-lg bg-status-success/15 border border-status-success/40 text-status-success hover:bg-status-success/25 transition-colors disabled:opacity-60"
              >
                <CheckCircle2 size={13} /> Clear Block
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="panel p-4">
        <h2 className="font-display text-sm text-ink mb-3">Event Timeline</h2>
        <div className="space-y-2 max-h-80 overflow-y-auto">
          {events.length === 0 && <p className="text-xs text-ink-faint">No hardware events yet.</p>}
          {events.map((e) => (
            <div
              key={e.id}
              className="flex items-center justify-between text-xs border-b border-panelBorder/40 last:border-0 py-2"
            >
              <div className="flex items-center gap-2">
                {e.event_type === "BLOCK_DETECTED" ? (
                  <AlertTriangle size={13} className="text-status-danger" />
                ) : (
                  <CheckCircle2 size={13} className="text-status-success" />
                )}
                <span className="text-ink">{e.event_type.replace("_", " ")}</span>
                <span className="text-ink-faint font-mono">Vehicle #{e.vehicle_id}</span>
              </div>
              <div className="flex items-center gap-3 text-ink-faint">
                <span>{e.status}</span>
                <span className="font-mono">{new Date(e.timestamp).toLocaleTimeString()}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
