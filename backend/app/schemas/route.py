from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.models.enums import TrafficMode


class RoutePoint(BaseModel):
    lat: float
    lng: float
    order_id: Optional[int] = None
    customer_name: Optional[str] = None
    sequence: Optional[int] = None


class RouteOut(BaseModel):
    id: int
    vehicle_id: int
    route_points: List[Dict[str, Any]]
    distance: float
    estimated_duration: float
    eta: Optional[str] = None
    traffic_mode: TrafficMode
    route_adherence: float
    optimization_score: float
    created_at: datetime

    class Config:
        from_attributes = True


class OptimizeRequest(BaseModel):
    order_ids: Optional[List[int]] = None  # None == optimize all unassigned orders
    traffic_mode: TrafficMode = TrafficMode.NORMAL


class OptimizeResult(BaseModel):
    routes_created: int
    vehicles_used: int
    orders_assigned: int
    orders_unassigned: int
    clusters_used: int
    total_distance: float
    routes: List[RouteOut]


class RecalculateRequest(BaseModel):
    vehicle_id: int
    traffic_mode: Optional[TrafficMode] = None
