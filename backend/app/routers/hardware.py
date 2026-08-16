from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.vehicle import Vehicle
from app.models.hardware_event import HardwareEvent
from app.schemas.hardware import (
    BlockRequest,
    BlockResponse,
    ClearResponse,
    HardwareEventOut,
)
from app.utils.deps import get_current_user, require_dispatcher
from app.hardware import rerouting_service

router = APIRouter(prefix="/hardware", tags=["Hardware"])


@router.post("/block/{vehicle_id}", response_model=BlockResponse)
def block_vehicle(
    vehicle_id: int,
    payload: BlockRequest = BlockRequest(),
    db: Session = Depends(get_db),
    _=Depends(require_dispatcher),
):
    """
    Simulates an ultrasonic sensor / hardware BLOCK_DETECTED signal.
    Only the affected vehicle reroutes (via A*); every other vehicle's
    route is untouched.
    """
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found.")

    result = rerouting_service.trigger_block(
        db, vehicle_id, latitude=payload.latitude, longitude=payload.longitude
    )
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return BlockResponse(**result)


@router.post("/clear/{vehicle_id}", response_model=ClearResponse)
def clear_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_dispatcher),
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found.")

    result = rerouting_service.trigger_clear(db, vehicle_id)
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return ClearResponse(**result)


@router.get("/events", response_model=List[HardwareEventOut])
def list_hardware_events(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(HardwareEvent).order_by(HardwareEvent.timestamp.desc()).limit(200).all()
