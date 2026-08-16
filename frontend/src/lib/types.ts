export type UserRole = "admin" | "dispatcher" | "rider";

export interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export type OrderPriority = "Normal" | "Express" | "Emergency";
export type OrderStatus =
  | "Unassigned"
  | "Assigned"
  | "In Progress"
  | "Completed"
  | "Delayed"
  | "Cancelled";
export type OrderSource = "CSV" | "JSON" | "Manual";

export interface Order {
  id: number;
  customer_name: string;
  phone_number?: string | null;
  address: string;
  latitude: number;
  longitude: number;
  priority: OrderPriority;
  time_window_start?: string | null;
  time_window_end?: string | null;
  package_weight: number;
  special_instructions?: string | null;
  status: OrderStatus;
  assigned_vehicle_id?: number | null;
  assigned_rider_id?: number | null;
  created_via: OrderSource;
  created_at: string;
}

export type VehicleStatus = "Idle" | "Active" | "Blocked" | "Offline";

export interface Vehicle {
  id: number;
  name: string;
  capacity: number;
  mileage: number;
  max_stops: number;
  driver_name?: string | null;
  status: VehicleStatus;
  current_latitude?: number | null;
  current_longitude?: number | null;
  current_eta?: string | null;
  fuel_consumption: number;
  co2_emissions: number;
}

export type TrafficMode = "Normal" | "Heavy" | "Accident";

export interface RoutePoint {
  lat: number;
  lng: number;
  order_id?: number | null;
  customer_name?: string | null;
  sequence?: number | null;
  detour?: boolean;
}

export interface RouteRecord {
  id: number;
  vehicle_id: number;
  route_points: RoutePoint[];
  distance: number;
  estimated_duration: number;
  eta?: string | null;
  traffic_mode: TrafficMode;
  route_adherence: number;
  optimization_score: number;
  created_at: string;
}

export interface OptimizeResult {
  routes_created: number;
  vehicles_used: number;
  orders_assigned: number;
  orders_unassigned: number;
  clusters_used: number;
  total_distance: number;
  routes: RouteRecord[];
}

export type HardwareEventType = "BLOCK_DETECTED" | "BLOCK_CLEARED";
export type HardwareEventStatus = "Active" | "Resolved";

export interface HardwareEvent {
  id: number;
  vehicle_id: number;
  event_type: HardwareEventType;
  latitude?: number | null;
  longitude?: number | null;
  previous_route?: RoutePoint[] | null;
  new_route?: RoutePoint[] | null;
  timestamp: string;
  status: HardwareEventStatus;
}

export interface BlockResponse {
  vehicle_id: number;
  rerouted: boolean;
  event_id?: number;
  route_id?: number | null;
  detour_distance_km?: number | null;
  new_total_distance_km?: number | null;
  new_eta?: string | null;
  new_fuel_consumption?: number | null;
  new_co2_emissions?: number | null;
  reason?: string | null;
}

export interface FleetStatus {
  total_vehicles: number;
  active_vehicles: number;
  total_fuel_used: number;
  total_co2_emissions: number;
}

export interface ETAPrediction {
  predicted_eta_minutes: number;
  expected_delay_minutes: number;
  confidence_percentage: number;
  model: string;
  model_trained_at?: string | null;
  model_mae_minutes?: number | null;
  note?: string | null;
}

export interface MLStatus {
  model_trained: boolean;
  training_samples_available: number;
  min_samples_required: number;
  metadata: Record<string, unknown>;
  optimization_engine: string;
  shortest_path_algorithm: string;
  eta_prediction_model: string;
}

export interface RiderPerformance {
  rider_id: number;
  rider_name: string;
  deliveries_completed: number;
  on_time_percentage: number;
  average_delay: number;
  route_adherence: number;
  efficiency_score: number;
  fuel_efficiency: number;
  updated_at: string;
}

export interface RouteHistoryEntry {
  id: number;
  vehicle_id: number;
  route?: RoutePoint[] | null;
  distance: number;
  eta_predicted?: number | null;
  eta_actual?: number | null;
  traffic_mode: TrafficMode;
  delay: number;
  fuel_consumption: number;
  co2_emissions: number;
  timestamp: string;
}

export interface UploadResult {
  created: number;
  failed: number;
  errors: string[];
  order_ids: number[];
}
