from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import VehicleStatus


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # e.g. Van-01
    capacity = Column(Float, nullable=False, default=100.0)  # kg
    mileage = Column(Float, nullable=False, default=12.0)  # km per litre
    max_stops = Column(Integer, nullable=False, default=25)
    driver_name = Column(String, nullable=True)
    status = Column(SAEnum(VehicleStatus), nullable=False, default=VehicleStatus.IDLE)

    current_latitude = Column(Float, nullable=True)
    current_longitude = Column(Float, nullable=True)
    current_eta = Column(String, nullable=True)

    fuel_consumption = Column(Float, nullable=False, default=0.0)  # litres
    co2_emissions = Column(Float, nullable=False, default=0.0)  # kg

    # optional link to a rider user account
    driver_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    orders = relationship("Order", back_populates="vehicle")
    routes = relationship("Route", back_populates="vehicle")
