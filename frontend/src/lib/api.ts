import axios from "axios";
import type {
  AuthResponse,
  User,
  Order,
  Vehicle,
  RouteRecord,
  OptimizeResult,
  HardwareEvent,
  BlockResponse,
  FleetStatus,
  ETAPrediction,
  MLStatus,
  UploadResult,
  TrafficMode,
  OrderPriority,
} from "./types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({ baseURL: API_URL });

const TOKEN_KEY = "routexai_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export interface ApiErrorShape {
  status?: number;
  message: string;
}

export function extractError(err: unknown): ApiErrorShape {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    const message = Array.isArray(detail)
      ? detail.map((d: any) => d.msg || JSON.stringify(d)).join("; ")
      : typeof detail === "string"
      ? detail
      : err.message;
    return { status: err.response?.status, message };
  }
  return { message: String(err) };
}

// --- Auth ---
export const authApi = {
  login: (email: string, password: string) =>
    api.post<AuthResponse>("/auth/login", { email, password }).then((r) => r.data),
  register: (name: string, email: string, password: string, role: string) =>
    api.post<AuthResponse>("/auth/register", { name, email, password, role }).then((r) => r.data),
  me: () => api.get<User>("/auth/me").then((r) => r.data),
};

// --- Orders ---
export interface ManualOrderPayload {
  customer_name: string;
  phone_number?: string;
  address: string;
  latitude: number;
  longitude: number;
  priority: OrderPriority;
  time_window_start?: string;
  time_window_end?: string;
  package_weight: number;
  special_instructions?: string;
}

export const ordersApi = {
  list: () => api.get<Order[]>("/orders").then((r) => r.data),
  get: (id: number) => api.get<Order>(`/orders/${id}`).then((r) => r.data),
  createManual: (order: ManualOrderPayload, optimize: boolean) =>
    api.post<Order>("/orders/manual", { order, optimize }).then((r) => r.data),
  upload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api
      .post<UploadResult>("/orders/upload", form, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      .then((r) => r.data);
  },
  update: (id: number, payload: Partial<Order>) =>
    api.put<Order>(`/orders/${id}`, payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/orders/${id}`),
};

// --- Fleet ---
export const fleetApi = {
  vehicles: () => api.get<Vehicle[]>("/fleet/vehicles").then((r) => r.data),
  vehicle: (id: number) => api.get<Vehicle>(`/fleet/vehicles/${id}`).then((r) => r.data),
  status: () => api.get<FleetStatus>("/fleet/status").then((r) => r.data),
  create: (payload: Partial<Vehicle>) =>
    api.post<Vehicle>("/fleet/vehicles", payload).then((r) => r.data),
};

// --- Routes ---
export const routesApi = {
  list: () => api.get<RouteRecord[]>("/routes").then((r) => r.data),
  optimize: (orderIds: number[] | undefined, trafficMode: TrafficMode) =>
    api
      .post<OptimizeResult>("/routes/optimize", { order_ids: orderIds ?? null, traffic_mode: trafficMode })
      .then((r) => r.data),
  recalculate: (vehicleId: number, trafficMode?: TrafficMode) =>
    api
      .post<OptimizeResult>("/routes/recalculate", { vehicle_id: vehicleId, traffic_mode: trafficMode })
      .then((r) => r.data),
};

// --- Hardware ---
export const hardwareApi = {
  block: (vehicleId: number, lat?: number, lng?: number) =>
    api
      .post<BlockResponse>(`/hardware/block/${vehicleId}`, { latitude: lat ?? null, longitude: lng ?? null })
      .then((r) => r.data),
  clear: (vehicleId: number) =>
    api.post(`/hardware/clear/${vehicleId}`).then((r) => r.data),
  events: () => api.get<HardwareEvent[]>("/hardware/events").then((r) => r.data),
};

// --- ML ---
export const mlApi = {
  eta: (distanceKm: number, trafficMode: TrafficMode, vehicleId?: number, numStops?: number) =>
    api
      .get<ETAPrediction>("/ml/eta", {
        params: { distance_km: distanceKm, traffic_mode: trafficMode, vehicle_id: vehicleId, num_stops: numStops },
      })
      .then((r) => r.data),
  status: () => api.get<MLStatus>("/ml/status").then((r) => r.data),
};

// --- Riders ---
export const ridersApi = {
  performance: () => api.get<import("./types").RiderPerformance[]>("/riders/performance").then((r) => r.data),
};

// --- Route history ---
export const routeHistoryApi = {
  list: (limit = 100) =>
    api
      .get<import("./types").RouteHistoryEntry[]>("/route-history", { params: { limit } })
      .then((r) => r.data),
};
