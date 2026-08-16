from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from app.models.enums import TrafficMode


class RouteHistoryCreate(BaseModel):
    """Records the outcome of a completed delivery — feeds the self-learning
    ETA feedback loop (predicted vs. actual)."""

    vehicle_id: int
    route: Optional[List[Dict[str, Any]]] = None
    distance: float = Field(..., ge=0)
    eta_predicted: Optional[float] = None  # minutes
    eta_actual: float = Field(..., ge=0)  # minutes
    traffic_mode: TrafficMode = TrafficMode.NORMAL
    fuel_consumption: float = Field(default=0.0, ge=0)
    co2_emissions: float = Field(default=0.0, ge=0)


class RouteHistoryOut(BaseModel):
    id: int
    vehicle_id: int
    route: Optional[List[Dict[str, Any]]] = None
    distance: float
    eta_predicted: Optional[float] = None
    eta_actual: Optional[float] = None
    traffic_mode: TrafficMode
    delay: float
    fuel_consumption: float
    co2_emissions: float
    timestamp: datetime

    class Config:
        from_attributes = True


class ETAPredictionRequest(BaseModel):
    distance_km: float = Field(..., gt=0)
    traffic_mode: TrafficMode = TrafficMode.NORMAL
    vehicle_id: Optional[int] = None
    num_stops: int = Field(default=1, ge=1)


class ETAPredictionResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    predicted_eta_minutes: float
    expected_delay_minutes: float
    confidence_percentage: float
    model: str
    model_trained_at: Optional[str] = None
    model_mae_minutes: Optional[float] = None
    note: Optional[str] = None
