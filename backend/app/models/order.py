from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    Text,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import OrderPriority, OrderStatus, OrderSource


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    address = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    priority = Column(
        SAEnum(OrderPriority), nullable=False, default=OrderPriority.NORMAL
    )
    time_window_start = Column(String, nullable=True)  # HH:MM
    time_window_end = Column(String, nullable=True)  # HH:MM

    package_weight = Column(Float, nullable=False, default=1.0)
    special_instructions = Column(Text, nullable=True)

    status = Column(
        SAEnum(OrderStatus), nullable=False, default=OrderStatus.UNASSIGNED
    )
    status_manually_set = Column(
        Integer, nullable=False, default=0
    )  # 0/1 flag: protects manual edits from auto-sync

    assigned_vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    assigned_rider_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_via = Column(SAEnum(OrderSource), nullable=False, default=OrderSource.MANUAL)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    vehicle = relationship("Vehicle", back_populates="orders")
