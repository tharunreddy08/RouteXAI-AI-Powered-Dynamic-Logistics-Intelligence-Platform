from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.models.enums import HardwareEventType, HardwareEventStatus


class BlockRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class HardwareEventOut(BaseModel):
    id: int
    vehicle_id: int
    event_type: HardwareEventType
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    previous_route: Optional[List[Dict[str, Any]]] = None
    new_route: Optional[List[Dict[str, Any]]] = None
    timestamp: datetime
    status: HardwareEventStatus

    class Config:
        from_attributes = True


class BlockResponse(BaseModel):
    vehicle_id: int
    rerouted: bool
    event_id: Optional[int] = None
    route_id: Optional[int] = None
    detour_distance_km: Optional[float] = None
    new_total_distance_km: Optional[float] = None
    new_eta: Optional[str] = None
    new_fuel_consumption: Optional[float] = None
    new_co2_emissions: Optional[float] = None
    reason: Optional[str] = None


class ClearResponse(BaseModel):
    vehicle_id: int
    cleared: bool
    event_id: Optional[int] = None
    route_recalculated: bool = False
