"""
Vehicle Routing Problem with Time Windows (VRPTW) solver using Google OR-Tools.

Given a depot, a set of orders (each with location, demand, time window, and
priority) and a set of vehicles (each with capacity and max stop count), this
produces one route per vehicle that:
  - respects vehicle capacity
  - respects each order's delivery time window
  - respects each vehicle's max stop count
  - prioritizes Emergency > Express > Normal orders when not everything can
    be feasibly served (soft constraint via drop penalties)

This module is deliberately separate from the DB layer — it operates on
plain dicts/lists so it's easy to unit test.
"""
from typing import List, Dict, Any, Optional
import logging

from ortools.constraint_solver import routing_enums_pb2, pywrapcp

from app.optimization.distance import build_distance_matrix, BASE_SPEED_KMPH

logger = logging.getLogger(__name__)

# Priority -> drop penalty. Higher penalty = optimizer will go to greater
# lengths (more distance/time) before it accepts leaving that order unserved.
PRIORITY_PENALTY = {
    "Normal": 5_000,
    "Express": 25_000,
    "Emergency": 100_000,
}

SERVICE_TIME_MINUTES = 5  # time spent at each stop (loading/handoff)
DEFAULT_TIME_WINDOW = (0, 24 * 60)  # whole-day window if none specified
SOLVE_TIME_LIMIT_SECONDS = 8


def _parse_time_window(start: Optional[str], end: Optional[str]) -> tuple:
    """Convert 'HH:MM' strings to (start_minute, end_minute) from midnight."""
    def to_minutes(t: Optional[str], default: int) -> int:
        if not t:
            return default
        try:
            h, m = t.split(":")
            return int(h) * 60 + int(m)
        except (ValueError, AttributeError):
            return default

    start_min = to_minutes(start, DEFAULT_TIME_WINDOW[0])
    end_min = to_minutes(end, DEFAULT_TIME_WINDOW[1])
    if end_min <= start_min:
        end_min = DEFAULT_TIME_WINDOW[1]
    return start_min, end_min


def solve_vrptw(
    depot: Dict[str, float],
    orders: List[Dict[str, Any]],
    vehicles: List[Dict[str, Any]],
    speed_kmph: float = BASE_SPEED_KMPH,
) -> Dict[str, Any]:
    """
    Args:
        depot: {"latitude": float, "longitude": float}
        orders: list of dicts with keys: id, latitude, longitude,
                package_weight, priority, time_window_start, time_window_end
        vehicles: list of dicts with keys: id, capacity, max_stops
        speed_kmph: assumed average travel speed, adjusted by caller for traffic

    Returns:
        {
          "assigned": {vehicle_id: [order_id, ...]},  # in visit order
          "unassigned_order_ids": [...],
          "route_points": {vehicle_id: [{"lat","lng","order_id","sequence"}]},
          "distance_km": {vehicle_id: float},
          "duration_minutes": {vehicle_id: float},
        }
    """
    if not orders or not vehicles:
        return {
            "assigned": {},
            "unassigned_order_ids": [o["id"] for o in orders],
            "route_points": {},
            "distance_km": {},
            "duration_minutes": {},
        }

    # Node 0 is always the depot.
    points = [(depot["latitude"], depot["longitude"])] + [
        (o["latitude"], o["longitude"]) for o in orders
    ]
    distance_matrix_km = build_distance_matrix(points)
    # OR-Tools wants integers; use meters.
    distance_matrix_m = [[int(round(d * 1000)) for d in row] for row in distance_matrix_km]

    num_locations = len(points)
    num_vehicles = len(vehicles)
    depot_index = 0

    manager = pywrapcp.RoutingIndexManager(num_locations, num_vehicles, depot_index)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix_m[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # --- Distance dimension (also used to derive travel time) ---
    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        10_000_000,  # generous max distance per vehicle (meters)
        True,  # start cumul at zero
        "Distance",
    )

    # --- Capacity dimension ---
    demands = [0] + [int(round(o.get("package_weight", 1.0) * 10)) for o in orders]  # scaled x10 for precision

    def demand_callback(from_index):
        node = manager.IndexToNode(from_index)
        return demands[node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    vehicle_capacities = [int(round(v.get("capacity", 250.0) * 10)) for v in vehicles]
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index, 0, vehicle_capacities, True, "Capacity"
    )

    # --- Max stops dimension (count of stops per vehicle) ---
    def stop_callback(from_index):
        node = manager.IndexToNode(from_index)
        return 0 if node == depot_index else 1

    stop_callback_index = routing.RegisterUnaryTransitCallback(stop_callback)
    max_stops_list = [int(v.get("max_stops", 25)) for v in vehicles]
    routing.AddDimensionWithVehicleCapacity(
        stop_callback_index, 0, max_stops_list, True, "Stops"
    )

    # --- Time dimension (minutes), with time windows ---
    speed_m_per_min = (speed_kmph * 1000) / 60.0

    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        travel_min = distance_matrix_m[from_node][to_node] / speed_m_per_min
        service_min = 0 if to_node == depot_index else SERVICE_TIME_MINUTES
        return int(round(travel_min + service_min))

    time_callback_index = routing.RegisterTransitCallback(time_callback)
    routing.AddDimension(
        time_callback_index,
        60,  # allow up to 60 min waiting slack at a stop
        24 * 60,  # max horizon: one day, in minutes
        False,
        "Time",
    )
    time_dimension = routing.GetDimensionOrDie("Time")

    time_windows = [DEFAULT_TIME_WINDOW] + [
        _parse_time_window(o.get("time_window_start"), o.get("time_window_end"))
        for o in orders
    ]
    for node in range(num_locations):
        index = manager.NodeToIndex(node)
        start, end = time_windows[node]
        time_dimension.CumulVar(index).SetRange(start, end)

    # --- Priority-weighted disjunctions: allow dropping low-priority orders
    # before high-priority ones when the problem is infeasible as a whole. ---
    for i, order in enumerate(orders):
        node = i + 1  # offset for depot
        index = manager.NodeToIndex(node)
        penalty = PRIORITY_PENALTY.get(order.get("priority", "Normal"), PRIORITY_PENALTY["Normal"])
        routing.AddDisjunction([index], penalty)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.FromSeconds(SOLVE_TIME_LIMIT_SECONDS)

    solution = routing.SolveWithParameters(search_parameters)

    result = {
        "assigned": {},
        "unassigned_order_ids": [],
        "route_points": {},
        "distance_km": {},
        "duration_minutes": {},
    }

    if solution is None:
        logger.warning("VRPTW solver found no solution; all orders left unassigned.")
        result["unassigned_order_ids"] = [o["id"] for o in orders]
        return result

    assigned_order_ids = set()

    for vehicle_idx in range(num_vehicles):
        vehicle_id = vehicles[vehicle_idx]["id"]
        index = routing.Start(vehicle_idx)
        route_order_ids: List[int] = []
        route_points: List[Dict[str, Any]] = []
        route_distance_m = 0
        sequence = 0

        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node != depot_index:
                order = orders[node - 1]
                route_order_ids.append(order["id"])
                assigned_order_ids.add(order["id"])
                route_points.append(
                    {
                        "lat": order["latitude"],
                        "lng": order["longitude"],
                        "order_id": order["id"],
                        "customer_name": order.get("customer_name"),
                        "sequence": sequence,
                    }
                )
                sequence += 1
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance_m += routing.GetArcCostForVehicle(previous_index, index, vehicle_idx)

        if route_order_ids:
            result["assigned"][vehicle_id] = route_order_ids
            result["route_points"][vehicle_id] = route_points
            result["distance_km"][vehicle_id] = round(route_distance_m / 1000.0, 2)
            result["duration_minutes"][vehicle_id] = round(
                (route_distance_m / 1000.0) / speed_kmph * 60
                + len(route_order_ids) * SERVICE_TIME_MINUTES,
                1,
            )

    all_order_ids = {o["id"] for o in orders}
    result["unassigned_order_ids"] = list(all_order_ids - assigned_order_ids)

    return result
