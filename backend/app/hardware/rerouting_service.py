"""
Hardware-based dynamic rerouting (spec section 16-17).

When a BLOCK_DETECTED signal arrives for a vehicle:
    1. log a HardwareEvent
    2. mark the vehicle blocked
    3. use A* to find an alternative path around the obstacle, from the
       vehicle's current position to its next stop
    4. splice that alternative path into the vehicle's active route
    5. recalculate ETA (via the ML model), fuel, and CO2 for that vehicle only
    6. every other vehicle's route is untouched — this module never queries
       or modifies vehicles other than the one passed in

When BLOCK_CLEARED arrives:
    1. log the clear event, resolve the open block event
    2. re-run route optimization for that vehicle's still-pending orders
       (the obstacle is gone, so the shortest path may look different again)
"""
from datetime import datetime
from typing import Optional, Dict, Any
import logging

from sqlalchemy.orm import Session

from app.models.vehicle import Vehicle
from app.models.route import Route
from app.models.order import Order
from app.models.hardware_event import HardwareEvent
from app.models.enums import (
    VehicleStatus,
    HardwareEventType,
    HardwareEventStatus,
    OrderStatus,
    TrafficMode,
)
from app.optimization.astar import find_path
from app.optimization.distance import road_distance_km
from app.ml import eta_model
from app.services.optimization_service import (
    TRAFFIC_FUEL_FACTOR,
    EMISSION_FACTOR_KG_PER_LITRE,
)

logger = logging.getLogger(__name__)

BLOCK_RADIUS_KM = 0.5


def _latest_active_route(db: Session, vehicle_id: int) -> Optional[Route]:
    return (
        db.query(Route)
        .filter(Route.vehicle_id == vehicle_id)
        .order_by(Route.created_at.desc())
        .first()
    )


def trigger_block(
    db: Session,
    vehicle_id: int,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> Dict[str, Any]:
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        return {"error": "vehicle_not_found"}

    route = _latest_active_route(db, vehicle_id)

    block_lat = latitude if latitude is not None else vehicle.current_latitude
    block_lng = longitude if longitude is not None else vehicle.current_longitude

    event = HardwareEvent(
        vehicle_id=vehicle_id,
        event_type=HardwareEventType.BLOCK_DETECTED,
        latitude=block_lat,
        longitude=block_lng,
        previous_route=route.route_points if route else None,
        new_route=None,
        status=HardwareEventStatus.ACTIVE,
    )
    db.add(event)
    vehicle.status = VehicleStatus.BLOCKED

    if not route or not route.route_points:
        # No active route to reroute — still log the event so the hardware
        # signal and vehicle status are accurately reflected.
        db.commit()
        db.refresh(event)
        return {
            "vehicle_id": vehicle_id,
            "rerouted": False,
            "reason": "no_active_route",
            "event_id": event.id,
        }

    start = (vehicle.current_latitude, vehicle.current_longitude)
    next_stop = route.route_points[0]
    end = (next_stop["lat"], next_stop["lng"])
    blocked_point = (block_lat, block_lng)

    astar_result = find_path(
        start=start,
        end=end,
        blocked_point=blocked_point,
        block_radius_km=BLOCK_RADIUS_KM,
    )

    # Original (pre-block) straight-line-estimated distance for this same
    # first leg, so we can compute the delta the detour adds to the route.
    original_leg_km = road_distance_km(start[0], start[1], end[0], end[1])
    detour_leg_km = astar_result["distance_km"]
    delta_km = max(detour_leg_km - original_leg_km, 0.0)

    new_total_distance = round(route.distance + delta_km, 2)

    # Splice: A* waypoints (informational, no order attached) followed by the
    # rest of the original route unchanged — only this vehicle's route moves.
    detour_waypoints = [
        {"lat": p[0], "lng": p[1], "order_id": None, "detour": True}
        for p in astar_result["path"][1:-1]  # exclude start/end, already represented
    ]
    new_route_points = detour_waypoints + route.route_points

    fuel_used = round(
        (new_total_distance / max(vehicle.mileage, 0.1))
        * TRAFFIC_FUEL_FACTOR.get(route.traffic_mode, 1.0),
        2,
    )
    co2 = round(fuel_used * EMISSION_FACTOR_KG_PER_LITRE, 2)

    eta_prediction = eta_model.predict(
        db,
        distance_km=new_total_distance,
        traffic_mode=route.traffic_mode.value if hasattr(route.traffic_mode, "value") else route.traffic_mode,
        vehicle_id=vehicle_id,
        num_stops=max(len([p for p in new_route_points if p.get("order_id")]), 1),
        vehicle_mileage=vehicle.mileage,
    )
    new_eta_minutes = eta_prediction["predicted_eta_minutes"]
    new_eta_str = f"{int(round(new_eta_minutes))} min"

    route.route_points = new_route_points
    route.distance = new_total_distance
    route.estimated_duration = new_eta_minutes
    route.eta = new_eta_str
    route.route_adherence = max(route.route_adherence - 5.0, 0.0)  # detour costs a little adherence

    vehicle.status = VehicleStatus.ACTIVE  # back underway, now on the detour
    vehicle.current_eta = new_eta_str
    vehicle.fuel_consumption = fuel_used
    vehicle.co2_emissions = co2

    event.new_route = new_route_points

    db.commit()
    db.refresh(route)
    db.refresh(event)
    db.refresh(vehicle)

    logger.info(
        "Hardware block rerouted vehicle %s: +%.2f km detour, new ETA %s",
        vehicle_id,
        delta_km,
        new_eta_str,
    )

    return {
        "vehicle_id": vehicle_id,
        "rerouted": True,
        "event_id": event.id,
        "route_id": route.id,
        "detour_distance_km": round(delta_km, 2),
        "new_total_distance_km": new_total_distance,
        "new_eta": new_eta_str,
        "new_fuel_consumption": fuel_used,
        "new_co2_emissions": co2,
        "astar_nodes_expanded": astar_result["nodes_expanded"],
        "astar_fallback_used": astar_result.get("fallback", False),
    }


def trigger_clear(db: Session, vehicle_id: int) -> Dict[str, Any]:
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        return {"error": "vehicle_not_found"}

    open_event = (
        db.query(HardwareEvent)
        .filter(
            HardwareEvent.vehicle_id == vehicle_id,
            HardwareEvent.event_type == HardwareEventType.BLOCK_DETECTED,
            HardwareEvent.status == HardwareEventStatus.ACTIVE,
        )
        .order_by(HardwareEvent.timestamp.desc())
        .first()
    )
    if open_event:
        open_event.status = HardwareEventStatus.RESOLVED

    clear_event = HardwareEvent(
        vehicle_id=vehicle_id,
        event_type=HardwareEventType.BLOCK_CLEARED,
        latitude=vehicle.current_latitude,
        longitude=vehicle.current_longitude,
        previous_route=None,
        new_route=None,
        status=HardwareEventStatus.RESOLVED,
    )
    db.add(clear_event)
    vehicle.status = VehicleStatus.ACTIVE
    db.commit()
    db.refresh(clear_event)

    # Obstacle is gone — re-optimize this vehicle's still-pending orders so
    # the route can return to its normal shortest path rather than staying
    # on the detour indefinitely.
    pending_order_ids = [
        o.id
        for o in db.query(Order)
        .filter(
            Order.assigned_vehicle_id == vehicle_id,
            Order.status.in_([OrderStatus.ASSIGNED, OrderStatus.IN_PROGRESS]),
        )
        .all()
    ]

    recalculated = False
    if pending_order_ids:
        from app.services.optimization_service import run_optimization

        # Temporarily free these orders so the optimizer can re-solve them;
        # run_optimization matches on explicit order_ids regardless of
        # current status, so this is safe. Restricted to this vehicle only
        # so the "only the affected vehicle changes" guarantee holds even
        # during the post-clear recalculation.
        result = run_optimization(db, order_ids=pending_order_ids, vehicle_ids=[vehicle_id])
        recalculated = result["routes_created"] > 0

    return {
        "vehicle_id": vehicle_id,
        "cleared": True,
        "event_id": clear_event.id,
        "route_recalculated": recalculated,
    }
