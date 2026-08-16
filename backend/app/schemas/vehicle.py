from typing import Optional
from pydantic import BaseModel, Field

from app.models.enums import VehicleStatus


class VehicleCreate(BaseModel):
    name: str = Field(..., min_length=1)
    capacity: float = Field(default=250.0, gt=0)
    mileage: float = Field(default=12.0, gt=0)
    max_stops: int = Field(default=25, gt=0)
    driver_name: Optional[str] = None
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None


class VehicleUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[float] = None
    mileage: Optional[float] = None
    max_stops: Optional[int] = None
    driver_name: Optional[str] = None
    status: Optional[VehicleStatus] = None
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None


class VehicleOut(BaseModel):
    id: int
    name: str
    capacity: float
    mileage: float
    max_stops: int
    driver_name: Optional[str] = None
    status: VehicleStatus
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    current_eta: Optional[str] = None
    fuel_consumption: float
    co2_emissions: float

    class Config:
        from_attributes = True
