from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class EmissionReport(Base):
    __tablename__ = "emission_reports"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=True)

    distance = Column(Float, nullable=False, default=0.0)
    fuel_used = Column(Float, nullable=False, default=0.0)
    emission_factor = Column(Float, nullable=False, default=2.68)  # kg CO2 per litre (diesel avg)
    co2_emissions = Column(Float, nullable=False, default=0.0)

    optimized_fuel = Column(Float, nullable=False, default=0.0)
    fuel_savings = Column(Float, nullable=False, default=0.0)
    co2_savings = Column(Float, nullable=False, default=0.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
