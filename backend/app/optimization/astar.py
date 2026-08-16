"""
A* shortest-path search.

Used for:
  - route refinement between two consecutive stops
  - alternative-path calculation when a hardware block event marks part of
    a route as obstructed (Phase 4)

There's no live road-network graph available, so this builds a local grid
graph over the bounding box between start and end (plus margin), with a
"blocked" cell (and its neighborhood) removed when routing around an
obstacle. This keeps the algorithm genuinely A* — real priority-queue graph
search with an admissible haversine heuristic — rather than faking it with
a straight line.
"""
import heapq
import math
from typing import List, Tuple, Optional, Dict

from app.optimization.distance import haversine_km

Point = Tuple[float, float]  # (lat, lng)


def _build_grid(
    start: Point, end: Point, resolution: int = 12, margin_ratio: float = 0.25
) -> List[List[Point]]:
    """Build a resolution x resolution grid of lat/lng points spanning the
    bounding box of start/end, expanded by margin_ratio on each side so the
    search has room to route around an obstacle rather than being boxed in.
    """
    lat_min, lat_max = sorted([start[0], end[0]])
    lng_min, lng_max = sorted([start[1], end[1]])

    lat_span = max(lat_max - lat_min, 0.01)
    lng_span = max(lng_max - lng_min, 0.01)

    lat_min -= lat_span * margin_ratio
    lat_max += lat_span * margin_ratio
    lng_min -= lng_span * margin_ratio
    lng_max += lng_span * margin_ratio

    grid = []
    for i in range(resolution):
        row = []
        for j in range(resolution):
            lat = lat_min + (lat_max - lat_min) * i / (resolution - 1)
            lng = lng_min + (lng_max - lng_min) * j / (resolution - 1)
            row.append((lat, lng))
        grid.append(row)
    return grid


def _nearest_cell(grid: List[List[Point]], point: Point) -> Tuple[int, int]:
    best, best_dist = (0, 0), float("inf")
    for i, row in enumerate(grid):
        for j, cell in enumerate(row):
            d = haversine_km(point[0], point[1], cell[0], cell[1])
            if d < best_dist:
                best_dist = d
                best = (i, j)
    return best


def find_path(
    start: Point,
    end: Point,
    blocked_point: Optional[Point] = None,
    block_radius_km: float = 0.4,
    resolution: int = 12,
) -> Dict:
    """
    Run A* over a local grid graph from start to end, optionally treating
    all grid cells within block_radius_km of blocked_point as obstacles.

    Returns:
        {"path": [(lat, lng), ...], "distance_km": float, "nodes_expanded": int}
    """
    grid = _build_grid(start, end, resolution=resolution)
    n = resolution

    def is_blocked(cell: Point) -> bool:
        if blocked_point is None:
            return False
        return haversine_km(cell[0], cell[1], blocked_point[0], blocked_point[1]) <= block_radius_km

    start_cell = _nearest_cell(grid, start)
    end_cell = _nearest_cell(grid, end)

    def neighbors(cell):
        i, j = cell
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di == 0 and dj == 0:
                    continue
                ni, nj = i + di, j + dj
                if 0 <= ni < n and 0 <= nj < n:
                    if not is_blocked(grid[ni][nj]):
                        yield (ni, nj)

    def h(cell):
        return haversine_km(grid[cell[0]][cell[1]][0], grid[cell[0]][cell[1]][1], end[0], end[1])

    def edge_cost(a, b):
        pa, pb = grid[a[0]][a[1]], grid[b[0]][b[1]]
        return haversine_km(pa[0], pa[1], pb[0], pb[1])

    open_heap = [(h(start_cell), 0.0, start_cell)]
    came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
    g_score = {start_cell: 0.0}
    visited = set()
    nodes_expanded = 0

    while open_heap:
        _, g, current = heapq.heappop(open_heap)
        if current in visited:
            continue
        visited.add(current)
        nodes_expanded += 1

        if current == end_cell:
            break

        for nb in neighbors(current):
            tentative_g = g + edge_cost(current, nb)
            if tentative_g < g_score.get(nb, math.inf):
                g_score[nb] = tentative_g
                came_from[nb] = current
                heapq.heappush(open_heap, (tentative_g + h(nb), tentative_g, nb))

    if end_cell not in came_from and end_cell != start_cell:
        # No path found (fully boxed in by the obstacle) — fall back to the
        # direct straight line so the caller always gets a usable route.
        return {
            "path": [start, end],
            "distance_km": haversine_km(start[0], start[1], end[0], end[1]),
            "nodes_expanded": nodes_expanded,
            "fallback": True,
        }

    # Reconstruct path.
    path_cells = [end_cell]
    cur = end_cell
    while cur != start_cell:
        cur = came_from[cur]
        path_cells.append(cur)
    path_cells.reverse()

    path_points = [start] + [grid[i][j] for (i, j) in path_cells] + [end]

    total_distance = 0.0
    for a, b in zip(path_points, path_points[1:]):
        total_distance += haversine_km(a[0], a[1], b[0], b[1])

    return {
        "path": path_points,
        "distance_km": round(total_distance, 3),
        "nodes_expanded": nodes_expanded,
        "fallback": False,
    }
