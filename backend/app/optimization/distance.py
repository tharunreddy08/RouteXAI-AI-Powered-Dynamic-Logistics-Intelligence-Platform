"""
Distance utilities shared by the clustering, VRPTW, and A* modules.

Real road-network distances would require a routing engine (OSRM, Google
Directions, etc). This app runs on haversine great-circle distance scaled by
a road-network detour factor (~1.3x), which is a standard approximation used
when a live routing API isn't available — clearly documented here rather
than presented as literal road distance.
"""
import math
from typing import List, Tuple

# Detour factor: real road distance is typically ~1.2-1.4x straight-line
# distance in urban areas. Used to keep ETA/fuel/CO2 estimates realistic.
ROAD_DETOUR_FACTOR = 1.3

# Average urban delivery-vehicle speed assumption for ETA estimation (km/h),
# adjusted per traffic mode in optimization/vrptw.py.
BASE_SPEED_KMPH = 28.0


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance between two lat/lng points, in kilometers."""
    R = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(a))


def road_distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Estimated road distance (haversine * detour factor)."""
    return haversine_km(lat1, lng1, lat2, lng2) * ROAD_DETOUR_FACTOR


def build_distance_matrix(points: List[Tuple[float, float]]) -> List[List[float]]:
    """Symmetric road-distance matrix (km) for a list of (lat, lng) points."""
    n = len(points)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = road_distance_km(points[i][0], points[i][1], points[j][0], points[j][1])
            matrix[i][j] = d
            matrix[j][i] = d
    return matrix
