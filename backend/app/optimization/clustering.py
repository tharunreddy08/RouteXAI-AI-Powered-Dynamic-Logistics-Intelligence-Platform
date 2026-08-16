"""
K-Means preprocessing stage: groups orders geographically into clusters
before handing each cluster to the OR-Tools VRPTW solver. This keeps the
optimizer's per-solve problem size small enough to stay fast as order counts
scale toward 1000+, per the RouteXAI architecture.
"""
import math
from typing import List, Dict, Any

import numpy as np
from sklearn.cluster import KMeans


def determine_cluster_count(
    num_orders: int,
    num_vehicles: int,
    avg_max_stops: int,
) -> int:
    """
    Dynamically size K based on fleet capacity, not a fixed constant.

    - Never exceeds the number of available vehicles (each cluster maps to
      at most one vehicle in the current single-depot design).
    - Scales up as order volume grows relative to per-vehicle stop capacity.
    - Always at least 1.
    """
    if num_orders == 0 or num_vehicles == 0:
        return 1

    stops_per_vehicle = max(avg_max_stops, 1)
    needed_by_volume = math.ceil(num_orders / stops_per_vehicle)

    k = max(1, min(num_vehicles, needed_by_volume))
    return k


def cluster_orders(
    orders: List[Dict[str, Any]],
    num_vehicles: int,
    avg_max_stops: int,
) -> Dict[int, List[Dict[str, Any]]]:
    """
    Cluster orders by (latitude, longitude) using K-Means.

    Args:
        orders: list of dicts, each must have 'id', 'latitude', 'longitude'.
        num_vehicles: number of vehicles available for assignment.
        avg_max_stops: average max_stops across those vehicles.

    Returns:
        dict mapping cluster_index -> list of order dicts in that cluster.
    """
    if not orders:
        return {}

    k = determine_cluster_count(len(orders), num_vehicles, avg_max_stops)

    if k == 1 or len(orders) <= k:
        return {0: orders}

    coords = np.array([[o["latitude"], o["longitude"]] for o in orders])
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(coords)

    clusters: Dict[int, List[Dict[str, Any]]] = {i: [] for i in range(k)}
    for order, label in zip(orders, labels):
        clusters[int(label)].append(order)

    # Drop empty clusters (can happen with skewed geography).
    return {idx: rows for idx, rows in clusters.items() if rows}
