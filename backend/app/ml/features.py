"""
Feature engineering for the ETA prediction model.

Feature vector order matters — it must be identical between training and
inference, so it's defined once here as FEATURE_NAMES and everything else
builds off it.
"""
from datetime import datetime
from typing import Optional

FEATURE_NAMES = [
    "distance_km",
    "traffic_mode_code",  # 0=Normal, 1=Heavy, 2=Accident
    "hour_of_day",
    "day_of_week",  # 0=Monday .. 6=Sunday
    "num_stops",
    "historical_avg_delay",
    "vehicle_mileage",
]

TRAFFIC_MODE_CODE = {"Normal": 0, "Heavy": 1, "Accident": 2}


def build_feature_vector(
    distance_km: float,
    traffic_mode: str,
    timestamp: Optional[datetime] = None,
    num_stops: int = 1,
    historical_avg_delay: float = 0.0,
    vehicle_mileage: float = 12.0,
) -> list:
    ts = timestamp or datetime.utcnow()
    return [
        float(distance_km),
        float(TRAFFIC_MODE_CODE.get(traffic_mode, 0)),
        float(ts.hour),
        float(ts.weekday()),
        float(num_stops),
        float(historical_avg_delay),
        float(vehicle_mileage),
    ]
