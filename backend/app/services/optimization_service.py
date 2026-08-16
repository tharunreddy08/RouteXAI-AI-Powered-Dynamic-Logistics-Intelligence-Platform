"""
Orchestrates the K-Means -> OR-Tools VRPTW pipeline and persists the result
as Route rows, updating Order and Vehicle state accordingly.

Pipeline (per spec section 10):
    Orders -> Geographical Preprocessing -> K-Means Clustering
    -> Cluster -> Vehicle Assignment -> OR-Tools VRPTW
    -> Optimized Multi-Vehicle Routes
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.vehicle import Vehicle
from app.models.route import Route
from app.models.enums import OrderStatus, VehicleStatus, TrafficMode
from app.optimization.clustering import cluster_orders
from app.optimization.vrptw import solve_vrptw
from app.optimization.distance import BASE_SPEED_KMPH
from app.ml import eta_model

# RouteXAI depot / warehouse location (Bengaluru), matches seed data geography.
DEPOT = {"latitude": 12.9716, "longitude": 77.5946}

# Traffic mode -> speed multiplier applied to the base travel speed.
TRAFFIC_SPEED_FACTOR = {
    TrafficMode.NORMAL: 1.0,
    TrafficMode.HEAVY: 0.6,
    TrafficMode.ACCIDENT: 0.35,
}

# Traffic mode -> fuel/CO2 penalty multiplier (congestion burns more fuel per km).
TRAFFIC_FUEL_FACTOR = {
    TrafficMode.NORMAL: 1.0,
    TrafficMode.HEAVY: 1.25,
    TrafficMode.ACCIDENT: 1.45,
}

EMISSION_FACTOR_KG_PER_LITRE = 2.68


def _order_to_dict(order: Order) -> Dict[str, Any]:
    return {
        "id": order.id,
        "latitude": order.latitude,
        "longitude": order.longitude,
        "package_weight": order.package_weight,
        "priority": order.priority.value,
        "time_window_start": order.time_window_start,
        "time_window_end": order.time_window_end,
        "customer_name": order.customer_name,
    }


def run_optimization(
    db: Session,
    order_ids: Optional[List[int]] = None,
    traffic_mode: TrafficMode = TrafficMode.NORMAL,
    vehicle_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    # 1. Pull candidate orders: explicit ids, or all currently unassigned ones.
    query = db.query(Order)
    if order_ids:
        query = query.filter(Order.id.in_(order_ids))
    else:
        query = query.filter(Order.status == OrderStatus.UNASSIGNED)
    orders = query.all()

    vehicle_query = db.query(Vehicle)
    if vehicle_ids:
        vehicle_query = vehicle_query.filter(Vehicle.id.in_(vehicle_ids))
    vehicles = vehicle_query.all()

    if not orders or not vehicles:
        return {
            "routes_created": 0,
            "vehicles_used": 0,
            "orders_assigned": 0,
            "orders_unassigned": len(orders),
            "clusters_used": 0,
            "total_distance": 0.0,
            "routes": [],
        }

    order_dicts = [_order_to_dict(o) for o in orders]
    orders_by_id = {o.id: o for o in orders}
    vehicles_by_id = {v.id: v for v in vehicles}

    avg_max_stops = round(sum(v.max_stops for v in vehicles) / len(vehicles))
    clusters = cluster_orders(order_dicts, num_vehicles=len(vehicles), avg_max_stops=avg_max_stops)

    speed = BASE_SPEED_KMPH * TRAFFIC_SPEED_FACTOR.get(traffic_mode, 1.0)

    # Distribute vehicles across clusters proportionally to cluster size, at
    # least one vehicle per non-empty cluster where possible.
    cluster_items = list(clusters.items())
    num_clusters = len(cluster_items)
    all_vehicle_dicts = [
        {"id": v.id, "capacity": v.capacity, "max_stops": v.max_stops} for v in vehicles
    ]

    routes_created: List[Route] = []
    total_orders_assigned = 0
    total_distance = 0.0
    vehicles_used = set()

    # Simple round-robin vehicle pool split across clusters so each cluster
    # gets its own dedicated sub-fleet rather than double-booking a vehicle.
    if num_clusters > 0:
        pool_size = max(1, len(all_vehicle_dicts) // num_clusters)
    else:
        pool_size = len(all_vehicle_dicts)

    for idx, (cluster_id, cluster_orders_list) in enumerate(cluster_items):
        start = idx * pool_size
        end = start + pool_size if idx < num_clusters - 1 else len(all_vehicle_dicts)
        cluster_vehicles = all_vehicle_dicts[start:end] or all_vehicle_dicts[:1]

        result = solve_vrptw(
            depot=DEPOT,
            orders=cluster_orders_list,
            vehicles=cluster_vehicles,
            speed_kmph=speed,
        )

        for vehicle_id, order_id_list in result["assigned"].items():
            vehicle = vehicles_by_id[vehicle_id]
            distance_km = result["distance_km"].get(vehicle_id, 0.0)
            duration_min = result["duration_minutes"].get(vehicle_id, 0.0)
            route_points = result["route_points"].get(vehicle_id, [])

            fuel_used = round(
                (distance_km / max(vehicle.mileage, 0.1))
                * TRAFFIC_FUEL_FACTOR.get(traffic_mode, 1.0),
                2,
            )
            co2 = round(fuel_used * EMISSION_FACTOR_KG_PER_LITRE, 2)

            # Prefer the trained ML ETA model once enough RouteHistory exists;
            # falls back to the VRPTW-derived duration otherwise (the
            # heuristic inside eta_model already accounts for this).
            eta_prediction = eta_model.predict(
                db,
                distance_km=distance_km,
                traffic_mode=traffic_mode.value,
                vehicle_id=vehicle_id,
                num_stops=max(len(order_id_list), 1),
                vehicle_mileage=vehicle.mileage,
            )
            eta_minutes = eta_prediction["predicted_eta_minutes"]
            eta_str = f"{int(round(eta_minutes))} min"

            route = Route(
                vehicle_id=vehicle_id,
                route_points=route_points,
                distance=distance_km,
                estimated_duration=duration_min,
                eta=eta_str,
                traffic_mode=traffic_mode,
                route_adherence=100.0,
                optimization_score=round(100 - (distance_km / max(len(order_id_list), 1)), 2),
            )
            db.add(route)
            routes_created.append(route)

            vehicle.status = VehicleStatus.ACTIVE
            vehicle.current_eta = eta_str
            vehicle.fuel_consumption = fuel_used
            vehicle.co2_emissions = co2
            if route_points:
                vehicle.current_latitude = route_points[0]["lat"]
                vehicle.current_longitude = route_points[0]["lng"]
            vehicles_used.add(vehicle_id)

            for order_id in order_id_list:
                order = orders_by_id[order_id]
                order.assigned_vehicle_id = vehicle_id
                order.assigned_rider_id = vehicle.driver_user_id
                if not order.status_manually_set:
                    order.status = OrderStatus.ASSIGNED

            total_orders_assigned += len(order_id_list)
            total_distance += distance_km

    db.commit()
    for route in routes_created:
        db.refresh(route)

    total_candidates = len(orders)
    return {
        "routes_created": len(routes_created),
        "vehicles_used": len(vehicles_used),
        "orders_assigned": total_orders_assigned,
        "orders_unassigned": total_candidates - total_orders_assigned,
        "clusters_used": num_clusters,
        "total_distance": round(total_distance, 2),
        "routes": routes_created,
    }
