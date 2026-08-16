from datetime import datetime
from pydantic import BaseModel


class RiderPerformanceOut(BaseModel):
    rider_id: int
    rider_name: str
    deliveries_completed: int
    on_time_percentage: float
    average_delay: float
    route_adherence: float
    efficiency_score: float
    fuel_efficiency: float
    updated_at: datetime

    class Config:
        from_attributes = True
