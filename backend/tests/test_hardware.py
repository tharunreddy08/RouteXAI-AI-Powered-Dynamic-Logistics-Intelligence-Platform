import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.models.vehicle import Vehicle
from app.models.route import Route
from app.models.hardware_event import HardwareEvent
from app.models.enums import VehicleStatus, TrafficMode, HardwareEventType, HardwareEventStatus
from app.hardware import rerouting_service


def _make_vehicle_with_route(db, name, base_lat, base_lng):
    vehicle = Vehicle(
        name=name,
        capacity=250,
        mileage=13,
        max_stops=25,
        status=VehicleStatus.ACTIVE,
        current_latitude=base_lat,
        current_longitude=base_lng,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    route = Route(
        vehicle_id=vehicle.id,
        route_points=[
            {"lat": base_lat + 0.05, "lng": base_lng + 0.05, "order_id": 9001, "sequence": 0},
            {"lat": base_lat + 0.08, "lng": base_lng + 0.08, "order_id": 9002, "sequence": 1},
        ],
        distance=12.0,
        estimated_duration=30.0,
        eta="30 min",
        traffic_mode=TrafficMode.NORMAL,
        route_adherence=100.0,
        optimization_score=90.0,
    )
    db.add(route)
    db.commit()
    db.refresh(route)
    return vehicle, route


def test_block_reroutes_only_the_affected_vehicle():
    db = SessionLocal()
    try:
        van_a, route_a = _make_vehicle_with_route(db, "Van-HW-A", 12.97, 77.59)
        van_b, route_b = _make_vehicle_with_route(db, "Van-HW-B", 13.05, 77.65)

        original_b_points = list(route_b.route_points)
        original_b_distance = route_b.distance

        blocked_point_lat = (van_a.current_latitude + route_a.route_points[0]["lat"]) / 2
        blocked_point_lng = (van_a.current_longitude + route_a.route_points[0]["lng"]) / 2

        result = rerouting_service.trigger_block(
            db, van_a.id, latitude=blocked_point_lat, longitude=blocked_point_lng
        )

        assert result["rerouted"] is True
        assert result["vehicle_id"] == van_a.id

        db.refresh(route_a)
        db.refresh(route_b)
        db.refresh(van_a)
        db.refresh(van_b)

        # Van A's route changed (detour spliced in, distance increased or equal).
        assert route_a.distance >= 12.0
        assert any(p.get("detour") for p in route_a.route_points)

        # Van B is completely untouched.
        assert route_b.route_points == original_b_points
        assert route_b.distance == original_b_distance
        assert van_b.status == VehicleStatus.ACTIVE

        # Original delivery stops for Van A are preserved (not dropped).
        remaining_order_ids = {p["order_id"] for p in route_a.route_points if p.get("order_id")}
        assert remaining_order_ids == {9001, 9002}

        # A HardwareEvent was logged.
        events = db.query(HardwareEvent).filter(HardwareEvent.vehicle_id == van_a.id).all()
        assert len(events) == 1
        assert events[0].event_type == HardwareEventType.BLOCK_DETECTED
        assert events[0].status == HardwareEventStatus.ACTIVE
    finally:
        db.close()


def test_clear_resolves_open_event_and_reactivates_vehicle():
    db = SessionLocal()
    try:
        vehicle, route = _make_vehicle_with_route(db, "Van-HW-C", 12.9, 77.5)

        rerouting_service.trigger_block(db, vehicle.id, latitude=12.91, longitude=77.51)
        db.refresh(vehicle)

        result = rerouting_service.trigger_clear(db, vehicle.id)
        assert result["cleared"] is True

        db.refresh(vehicle)
        assert vehicle.status == VehicleStatus.ACTIVE

        open_events = (
            db.query(HardwareEvent)
            .filter(
                HardwareEvent.vehicle_id == vehicle.id,
                HardwareEvent.event_type == HardwareEventType.BLOCK_DETECTED,
                HardwareEvent.status == HardwareEventStatus.ACTIVE,
            )
            .all()
        )
        assert len(open_events) == 0  # resolved

        clear_events = (
            db.query(HardwareEvent)
            .filter(
                HardwareEvent.vehicle_id == vehicle.id,
                HardwareEvent.event_type == HardwareEventType.BLOCK_CLEARED,
            )
            .all()
        )
        assert len(clear_events) == 1
    finally:
        db.close()


def test_block_on_vehicle_with_no_route_still_logs_event():
    db = SessionLocal()
    try:
        vehicle = Vehicle(
            name="Van-HW-NoRoute",
            capacity=250,
            mileage=13,
            max_stops=25,
            status=VehicleStatus.IDLE,
            current_latitude=12.9,
            current_longitude=77.6,
        )
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)

        result = rerouting_service.trigger_block(db, vehicle.id)
        assert result["rerouted"] is False
        assert result["reason"] == "no_active_route"

        events = db.query(HardwareEvent).filter(HardwareEvent.vehicle_id == vehicle.id).all()
        assert len(events) == 1
    finally:
        db.close()
