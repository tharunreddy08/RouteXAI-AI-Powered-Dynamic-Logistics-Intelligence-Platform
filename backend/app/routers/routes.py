from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.route import Route
from app.models.vehicle import Vehicle
from app.schemas.route import RouteOut, OptimizeRequest, OptimizeResult, RecalculateRequest
from app.utils.deps import get_current_user, require_dispatcher
from app.services.optimization_service import run_optimization

router = APIRouter(prefix="/routes", tags=["Routes"])


@router.post("/optimize", response_model=OptimizeResult)
def optimize_routes(
    payload: OptimizeRequest,
    db: Session = Depends(get_db),
    _=Depends(require_dispatcher),
):
    """
    Runs the K-Means -> OR-Tools VRPTW pipeline over the given order ids
    (or all currently unassigned orders if none are given), respecting
    vehicle capacity, max stops, time windows, and priority weighting.
    """
    result = run_optimization(db, order_ids=payload.order_ids, traffic_mode=payload.traffic_mode)
    return OptimizeResult(
        routes_created=result["routes_created"],
        vehicles_used=result["vehicles_used"],
        orders_assigned=result["orders_assigned"],
        orders_unassigned=result["orders_unassigned"],
        clusters_used=result["clusters_used"],
        total_distance=result["total_distance"],
        routes=[RouteOut.model_validate(r) for r in result["routes"]],
    )


@router.get("", response_model=List[RouteOut])
def list_routes(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Route).order_by(Route.created_at.desc()).all()


@router.get("/{route_id}", response_model=RouteOut)
def get_route(route_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found.")
    return route


@router.post("/recalculate", response_model=OptimizeResult)
def recalculate_route(
    payload: RecalculateRequest,
    db: Session = Depends(get_db),
    _=Depends(require_dispatcher),
):
    """
    Re-runs optimization for a single vehicle's currently assigned (not yet
    completed) orders — e.g. after a traffic mode change. Full A*-based
    single-vehicle rerouting around a hardware-detected obstacle is handled
    separately by the hardware block/clear endpoints (Phase 4).
    """
    vehicle = db.query(Vehicle).filter(Vehicle.id == payload.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found.")

    from app.models.order import Order
    from app.models.enums import OrderStatus

    order_ids = [
        o.id
        for o in db.query(Order)
        .filter(
            Order.assigned_vehicle_id == payload.vehicle_id,
            Order.status.in_([OrderStatus.ASSIGNED, OrderStatus.IN_PROGRESS]),
        )
        .all()
    ]
    if not order_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This vehicle has no active orders to recalculate.",
        )

    traffic_mode = payload.traffic_mode or db.query(Route).filter(
        Route.vehicle_id == payload.vehicle_id
    ).order_by(Route.created_at.desc()).first().traffic_mode

    result = run_optimization(
        db, order_ids=order_ids, traffic_mode=traffic_mode, vehicle_ids=[payload.vehicle_id]
    )
    return OptimizeResult(
        routes_created=result["routes_created"],
        vehicles_used=result["vehicles_used"],
        orders_assigned=result["orders_assigned"],
        orders_unassigned=result["orders_unassigned"],
        clusters_used=result["clusters_used"],
        total_distance=result["total_distance"],
        routes=[RouteOut.model_validate(r) for r in result["routes"]],
    )
