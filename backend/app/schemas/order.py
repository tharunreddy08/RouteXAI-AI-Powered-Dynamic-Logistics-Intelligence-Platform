from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

from app.models.enums import OrderPriority, OrderStatus, OrderSource


class OrderCreate(BaseModel):
    """Used for manual order entry and as the row shape for CSV/JSON upload."""

    customer_name: str = Field(..., min_length=1)
    phone_number: Optional[str] = None
    address: str = Field(..., min_length=1)
    latitude: float
    longitude: float
    priority: OrderPriority = OrderPriority.NORMAL
    time_window_start: Optional[str] = None
    time_window_end: Optional[str] = None
    package_weight: float = Field(default=1.0, gt=0)
    special_instructions: Optional[str] = None

    @field_validator("latitude")
    @classmethod
    def validate_lat(cls, v):
        if not -90 <= v <= 90:
            raise ValueError("latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_lng(cls, v):
        if not -180 <= v <= 180:
            raise ValueError("longitude must be between -180 and 180")
        return v


class OrderUpdate(BaseModel):
    customer_name: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    priority: Optional[OrderPriority] = None
    time_window_start: Optional[str] = None
    time_window_end: Optional[str] = None
    package_weight: Optional[float] = None
    special_instructions: Optional[str] = None
    status: Optional[OrderStatus] = None


class ManualOrderRequest(BaseModel):
    order: OrderCreate
    optimize: bool = False  # True == "Save & Optimize" button behavior


class UploadResult(BaseModel):
    created: int
    failed: int
    errors: List[str] = []
    order_ids: List[int] = []


class OrderOut(BaseModel):
    id: int
    customer_name: str
    phone_number: Optional[str] = None
    address: str
    latitude: float
    longitude: float
    priority: OrderPriority
    time_window_start: Optional[str] = None
    time_window_end: Optional[str] = None
    package_weight: float
    special_instructions: Optional[str] = None
    status: OrderStatus
    assigned_vehicle_id: Optional[int] = None
    assigned_rider_id: Optional[int] = None
    created_via: OrderSource
    created_at: datetime

    class Config:
        from_attributes = True
