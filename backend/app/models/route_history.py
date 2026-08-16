from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Enum as SAEnum, JSON
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import TrafficMode


class RouteHistory(Base):
    __tablename__ = "route_history"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    route = Column(JSON, nullable=True)  # snapshot of route_points

    distance = Column(Float, nullable=False, default=0.0)
    eta_predicted = Column(Float, nullable=True)  # minutes
    eta_actual = Column(Float, nullable=True)  # minutes

    traffic_mode = Column(SAEnum(TrafficMode), nullable=False, default=TrafficMode.NORMAL)
    delay = Column(Float, nullable=False, default=0.0)  # minutes
    fuel_consumption = Column(Float, nullable=False, default=0.0)
    co2_emissions = Column(Float, nullable=False, default=0.0)

    timestamp = Column(DateTime(timezone=True), server_default=func.now())
