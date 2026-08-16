from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    JSON,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import TrafficMode


class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)

    # list of {lat, lng, order_id?} points, stored as JSON
    route_points = Column(JSON, nullable=False, default=list)

    distance = Column(Float, nullable=False, default=0.0)  # km
    estimated_duration = Column(Float, nullable=False, default=0.0)  # minutes
    eta = Column(String, nullable=True)

    traffic_mode = Column(SAEnum(TrafficMode), nullable=False, default=TrafficMode.NORMAL)
    route_adherence = Column(Float, nullable=False, default=100.0)  # %
    optimization_score = Column(Float, nullable=False, default=0.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    vehicle = relationship("Vehicle", back_populates="routes")
