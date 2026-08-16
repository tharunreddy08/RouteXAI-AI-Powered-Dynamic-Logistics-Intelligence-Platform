import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polyline } from "react-leaflet";
import L from "leaflet";
import { Sparkles, Truck } from "lucide-react";
import { fleetApi, ordersApi, routesApi, extractError } from "../lib/api";
import type { Vehicle, Order, RouteRecord, TrafficMode } from "../lib/types";
import { VehicleStatusBadge } from "../components/Badges";
import { useToast } from "../lib/toast";

const ROUTE_COLORS: Record<number, string> = {
  1: "#3ee6c4",
  2: "#f5a623",
  3: "#c792ea",
  4: "#5ec8f5",
  5: "#ff7a7a",
};

function colorForVehicle(vehicleId: number) {
  const keys = Object.keys(ROUTE_COLORS).map(Number);
  return ROUTE_COLORS[keys[(vehicleId - 1) % keys.length]];
}

function vanIcon(color: string) {
  return L.divIcon({
    className: "",
    html: `<div style="
      width:16px;height:16px;border-radius:50%;
      background:${color};
      box-shadow:0 0 0 3px ${color}33, 0 0 10px ${color}aa;
      border:2px solid #0a0e16;
    "></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });
}

function orderIcon(priority: Order["priority"]) {
  const color = priority === "Emergency" ? "#ff5d5d" : priority === "Express" ? "#f5a623" : "#7c8aa3";
  return L.divIcon({
    className: "",
    html: `<div style="width:9px;height:9px;border-radius:2px;background:${color};transform:rotate(45deg);border:1px solid #0a0e1699;"></div>`,
    iconSize: [9, 9],
    iconAnchor: [4, 4],
  });
}

export default function FleetMapPage() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [routes, setRoutes] = useState<RouteRecord[]>([]);
  const [traffic, setTraffic] = useState<TrafficMode>("Normal");
  const [optimizing, setOptimizing] = useState(false);
  const { push } = useToast();

  function load() {
    Promise.all([fleetApi.vehicles(), ordersApi.list(), routesApi.list()]).then(
      ([v, o, r]) => {
        setVehicles(v);
        setOrders(o);
        setRoutes(r);
      }
    );
  }

  useEffect(load, []);

  async function handleOptimize() {
    setOptimizing(true);
    try {
      const result = await routesApi.optimize(undefined, traffic);
      push("success", `${result.routes_created} routes created under ${traffic} traffic.`);
      load();
    } catch (err) {
      push("error", extractError(err).message);
    } finally {
      setOptimizing(false);
    }
  }

  const center: [number, number] = [12.9716, 77.5946];
  const latestRouteByVehicle = new Map<number, RouteRecord>();
  for (const r of routes) {
    const existing = latestRouteByVehicle.get(r.vehicle_id);
    if (!existing || new Date(r.created_at) > new Date(existing.created_at)) {
      latestRouteByVehicle.set(r.vehicle_id, r);
    }
  }

  return (
    <div className="space-y-4 h-full flex flex-col">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-display text-xl text-ink">Fleet &amp; Map</h1>
          <p className="text-sm text-ink-faint mt-1">{vehicles.length} vehicles · {orders.length} orders</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={traffic}
            onChange={(e) => setTraffic(e.target.value as TrafficMode)}
            className="input w-auto"
          >
            <option value="Normal">Normal Traffic</option>
            <option value="Heavy">Heavy Traffic</option>
            <option value="Accident">Accident</option>
          </select>
          <button
            onClick={handleOptimize}
            disabled={optimizing}
            className="flex items-center gap-1.5 text-sm px-3 py-2 rounded-lg bg-signal/15 border border-signal/40 text-signal hover:bg-signal/25 transition-colors disabled:opacity-60"
          >
            <Sparkles size={15} /> {optimizing ? "Optimizing…" : "Re-optimize Routes"}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 flex-1 min-h-[560px]">
        <div className="lg:col-span-3 panel overflow-hidden">
          <MapContainer center={center} zoom={12} style={{ height: "100%", width: "100%", minHeight: 560 }}>
            <TileLayer
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              attribution='&copy; OpenStreetMap &copy; CARTO'
            />
            {vehicles.map((v) =>
              v.current_latitude && v.current_longitude ? (
                <Marker
                  key={`v-${v.id}`}
                  position={[v.current_latitude, v.current_longitude]}
                  icon={vanIcon(colorForVehicle(v.id))}
                >
                  <Popup>
                    <div className="text-xs space-y-1">
                      <div className="font-semibold">{v.name}</div>
                      <div>Driver: {v.driver_name || "—"}</div>
                      <div>Status: {v.status}</div>
                      <div>ETA: {v.current_eta || "—"}</div>
                      <div>Fuel: {v.fuel_consumption.toFixed(1)} L</div>
                      <div>CO2: {v.co2_emissions.toFixed(1)} kg</div>
                    </div>
                  </Popup>
                </Marker>
              ) : null
            )}
            {orders.map((o) => (
              <Marker key={`o-${o.id}`} position={[o.latitude, o.longitude]} icon={orderIcon(o.priority)}>
                <Popup>
                  <div className="text-xs space-y-1">
                    <div className="font-semibold">{o.customer_name}</div>
                    <div>{o.address}</div>
                    <div>Priority: {o.priority}</div>
                    <div>Status: {o.status}</div>
                  </div>
                </Popup>
              </Marker>
            ))}
            {[...latestRouteByVehicle.entries()].map(([vehicleId, route]) => (
              <Polyline
                key={`r-${route.id}`}
                positions={route.route_points.map((p) => [p.lat, p.lng] as [number, number])}
                pathOptions={{ color: colorForVehicle(vehicleId), weight: 3, opacity: 0.8 }}
              />
            ))}
          </MapContainer>
        </div>

        <div className="panel p-4 overflow-y-auto space-y-3">
          <h2 className="font-display text-sm text-ink flex items-center gap-2">
            <Truck size={14} className="text-signal" /> Vehicles
          </h2>
          {vehicles.map((v) => {
            const route = latestRouteByVehicle.get(v.id);
            return (
              <div key={v.id} className="rounded-lg border border-panelBorder/60 bg-base-800/50 p-3">
                <div className="flex items-center justify-between mb-1.5">
                  <span
                    className="font-mono text-sm"
                    style={{ color: colorForVehicle(v.id) }}
                  >
                    {v.name}
                  </span>
                  <VehicleStatusBadge status={v.status} />
                </div>
                <div className="text-xs text-ink-faint space-y-0.5">
                  <div>Driver: {v.driver_name || "—"}</div>
                  <div>ETA: {v.current_eta || "—"}</div>
                  {route && (
                    <>
                      <div>Distance: {route.distance.toFixed(1)} km</div>
                      <div>Stops: {route.route_points.filter((p) => p.order_id).length}</div>
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
