from sqlalchemy import (
    Column,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    JSON,
)
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import HardwareEventType, HardwareEventStatus


class HardwareEvent(Base):
    __tablename__ = "hardware_events"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    event_type = Column(SAEnum(HardwareEventType), nullable=False)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    previous_route = Column(JSON, nullable=True)
    new_route = Column(JSON, nullable=True)

    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(
        SAEnum(HardwareEventStatus), nullable=False, default=HardwareEventStatus.ACTIVE
    )
