from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleOut, VehicleCreate, VehicleUpdate
from app.utils.deps import get_current_user, require_dispatcher

router = APIRouter(prefix="/fleet", tags=["Fleet"])


@router.get("/vehicles", response_model=List[VehicleOut])
def list_vehicles(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Vehicle).all()


@router.post("/vehicles", response_model=VehicleOut, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    payload: VehicleCreate,
    db: Session = Depends(get_db),
    _=Depends(require_dispatcher),
):
    existing = db.query(Vehicle).filter(Vehicle.name == payload.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A vehicle named '{payload.name}' already exists.",
        )
    vehicle = Vehicle(**payload.model_dump())
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.get("/vehicles/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found.")
    return vehicle


@router.put("/vehicles/{vehicle_id}", response_model=VehicleOut)
def update_vehicle(
    vehicle_id: int,
    payload: VehicleUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_dispatcher),
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(vehicle, field, value)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.delete("/vehicles/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_dispatcher),
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found.")
    db.delete(vehicle)
    db.commit()
    return None


@router.get("/status")
def fleet_status(db: Session = Depends(get_db), _=Depends(get_current_user)):
    vehicles = db.query(Vehicle).all()
    total_vehicles = len(vehicles)
    active_vehicles = len([v for v in vehicles if v.status.value == "Active"])
    total_fuel = sum(v.fuel_consumption for v in vehicles)
    total_co2 = sum(v.co2_emissions for v in vehicles)

    return {
        "total_vehicles": total_vehicles,
        "active_vehicles": active_vehicles,
        "total_fuel_used": round(total_fuel, 2),
        "total_co2_emissions": round(total_co2, 2),
    }
