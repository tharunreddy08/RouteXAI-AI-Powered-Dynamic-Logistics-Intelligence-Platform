from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class RiderPerformance(Base):
    __tablename__ = "rider_performance"

    id = Column(Integer, primary_key=True, index=True)
    rider_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    deliveries_completed = Column(Integer, nullable=False, default=0)
    on_time_percentage = Column(Float, nullable=False, default=100.0)
    average_delay = Column(Float, nullable=False, default=0.0)  # minutes
    route_adherence = Column(Float, nullable=False, default=100.0)  # %
    efficiency_score = Column(Float, nullable=False, default=0.0)
    fuel_efficiency = Column(Float, nullable=False, default=0.0)

    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    rider = relationship("User", back_populates="rider_performance")
