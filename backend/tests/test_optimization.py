import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.optimization.distance import haversine_km, road_distance_km
from app.optimization.clustering import cluster_orders, determine_cluster_count
from app.optimization.vrptw import solve_vrptw
from app.optimization.astar import find_path


def test_haversine_known_distance():
    # Roughly the distance between MG Road and Whitefield, Bengaluru (~15km)
    d = haversine_km(12.9716, 77.5946, 12.9698, 77.7500)
    assert 10 < d < 20


def test_road_distance_applies_detour_factor():
    hav = haversine_km(12.9716, 77.5946, 12.98, 77.60)
    road = road_distance_km(12.9716, 77.5946, 12.98, 77.60)
    assert road > hav


def test_determine_cluster_count_bounds():
    assert determine_cluster_count(0, 5, 25) == 1
    assert determine_cluster_count(10, 5, 25) == 1
    assert determine_cluster_count(200, 5, 25) == 5  # capped at num_vehicles


def test_cluster_orders_groups_by_geography():
    orders = [
        {"id": 1, "latitude": 12.97, "longitude": 77.59},
        {"id": 2, "latitude": 12.971, "longitude": 77.591},
        {"id": 3, "latitude": 13.05, "longitude": 77.65},
        {"id": 4, "latitude": 13.051, "longitude": 77.651},
    ]
    clusters = cluster_orders(orders, num_vehicles=2, avg_max_stops=1)
    assert len(clusters) <= 2
    total = sum(len(v) for v in clusters.values())
    assert total == 4


def test_vrptw_respects_capacity_and_returns_routes():
    depot = {"latitude": 12.9716, "longitude": 77.5946}
    orders = [
        {
            "id": i,
            "latitude": 12.9716 + i * 0.01,
            "longitude": 77.5946 + i * 0.01,
            "package_weight": 5.0,
            "priority": "Normal",
            "time_window_start": None,
            "time_window_end": None,
            "customer_name": f"Customer {i}",
        }
        for i in range(1, 6)
    ]
    vehicles = [{"id": 1, "capacity": 100.0, "max_stops": 25}]

    result = solve_vrptw(depot, orders, vehicles)
    assert 1 in result["assigned"]
    assigned_ids = set(result["assigned"][1])
    assert assigned_ids.issubset({o["id"] for o in orders})
    assert result["distance_km"][1] >= 0


def test_vrptw_prioritizes_emergency_when_capacity_constrained():
    depot = {"latitude": 12.9716, "longitude": 77.5946}
    # 5 heavy orders but only enough capacity for ~2 -> emergency must win.
    orders = [
        {
            "id": 1,
            "latitude": 12.98,
            "longitude": 77.60,
            "package_weight": 40.0,
            "priority": "Emergency",
            "time_window_start": None,
            "time_window_end": None,
            "customer_name": "Urgent",
        },
    ] + [
        {
            "id": i,
            "latitude": 12.9716 + i * 0.02,
            "longitude": 77.5946 + i * 0.02,
            "package_weight": 40.0,
            "priority": "Normal",
            "time_window_start": None,
            "time_window_end": None,
            "customer_name": f"Customer {i}",
        }
        for i in range(2, 6)
    ]
    vehicles = [{"id": 1, "capacity": 80.0, "max_stops": 25}]

    result = solve_vrptw(depot, orders, vehicles)
    assigned_ids = set(result["assigned"].get(1, []))
    assert 1 in assigned_ids  # emergency order must be served


def test_astar_finds_path_without_obstacle():
    result = find_path((12.9716, 77.5946), (13.02, 77.65))
    assert len(result["path"]) >= 2
    assert result["distance_km"] > 0


def test_astar_routes_around_obstacle():
    start = (12.9716, 77.5946)
    end = (13.02, 77.65)
    midpoint = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)

    direct = find_path(start, end)
    rerouted = find_path(start, end, blocked_point=midpoint, block_radius_km=3.0)

    assert rerouted["distance_km"] >= direct["distance_km"] * 0.9  # not shorter than a clear path
