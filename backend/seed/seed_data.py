"""
Seed the database with demo data so RouteXAI works immediately after setup.

Run with:
    python -m seed.seed_data
"""
import random
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Base, engine, SessionLocal
from app import models  # noqa: F401
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.order import Order
from app.models.rider_performance import RiderPerformance
from app.models.route_history import RouteHistory
from app.models.emission_report import EmissionReport
from app.models.hardware_event import HardwareEvent
from app.models.enums import (
    UserRole,
    OrderPriority,
    OrderStatus,
    OrderSource,
    VehicleStatus,
    TrafficMode,
    HardwareEventType,
    HardwareEventStatus,
)
from app.utils.security import hash_password
from app.ml import eta_model

# Bengaluru-area coordinates for realistic demo geography.
BASE_LAT, BASE_LNG = 12.9716, 77.5946

CUSTOMER_NAMES = [
    "Ananya Rao", "Rohan Mehta", "Priya Nair", "Karan Singh", "Sneha Patil",
    "Vikram Joshi", "Divya Iyer", "Arjun Kumar", "Meera Pillai", "Aditya Shah",
    "Kavya Reddy", "Nikhil Verma", "Pooja Desai", "Sameer Khan", "Ritika Gupta",
    "Manoj Pillai", "Neha Kapoor", "Suresh Babu", "Anjali Menon", "Rahul Chawla",
]

ADDRESSES = [
    "MG Road", "Koramangala 5th Block", "Indiranagar 100ft Road", "Whitefield Main Road",
    "HSR Layout Sector 2", "Jayanagar 4th Block", "Electronic City Phase 1",
    "Marathahalli Bridge", "BTM Layout 2nd Stage", "Malleshwaram 8th Cross",
    "Yeshwanthpur", "Banashankari 3rd Stage", "JP Nagar 6th Phase", "Hebbal",
    "RT Nagar", "Sarjapur Road", "Rajajinagar", "Basavanagudi", "Domlur", "Ulsoor",
]


def random_offset():
    return random.uniform(-0.08, 0.08)


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        if db.query(User).count() > 0:
            print("Database already seeded — skipping. Delete routexai.db to reseed.")
            return

        print("Seeding users...")
        users = [
            User(
                name="Admin User",
                email="admin@routexai.com",
                password_hash=hash_password("Admin@123"),
                role=UserRole.ADMIN,
            ),
            User(
                name="Dispatcher User",
                email="dispatcher@routexai.com",
                password_hash=hash_password("Dispatch@123"),
                role=UserRole.DISPATCHER,
            ),
        ]
        rider_names = ["Ravi Kumar", "Ali Hassan", "Suman Das", "Deepak Rao", "Farhan Ahmed"]
        for i, rname in enumerate(rider_names, start=1):
            users.append(
                User(
                    name=rname,
                    email=f"rider{i}@routexai.com",
                    password_hash=hash_password("Rider@123"),
                    role=UserRole.RIDER,
                )
            )
        db.add_all(users)
        db.commit()
        for u in users:
            db.refresh(u)

        riders = [u for u in users if u.role == UserRole.RIDER]

        print("Seeding vehicles...")
        vehicle_defs = [
            ("Van-01", 250.0, 14.0, 25),
            ("Van-02", 250.0, 13.5, 25),
            ("Van-03", 300.0, 12.0, 30),
            ("Van-04", 200.0, 15.0, 20),
            ("Van-05", 300.0, 12.5, 30),
        ]
        vehicles = []
        for i, (name, capacity, mileage, max_stops) in enumerate(vehicle_defs):
            driver = riders[i % len(riders)]
            vehicles.append(
                Vehicle(
                    name=name,
                    capacity=capacity,
                    mileage=mileage,
                    max_stops=max_stops,
                    driver_name=driver.name,
                    driver_user_id=driver.id,
                    status=VehicleStatus.IDLE,
                    current_latitude=BASE_LAT + random_offset(),
                    current_longitude=BASE_LNG + random_offset(),
                    current_eta=None,
                    fuel_consumption=round(random.uniform(5, 20), 2),
                    co2_emissions=round(random.uniform(15, 55), 2),
                )
            )
        db.add_all(vehicles)
        db.commit()
        for v in vehicles:
            db.refresh(v)

        print("Seeding orders...")
        priorities = (
            [OrderPriority.NORMAL] * 6 + [OrderPriority.EXPRESS] * 3 + [OrderPriority.EMERGENCY] * 1
        )
        statuses = (
            [OrderStatus.UNASSIGNED] * 3
            + [OrderStatus.ASSIGNED] * 3
            + [OrderStatus.IN_PROGRESS] * 2
            + [OrderStatus.COMPLETED] * 3
            + [OrderStatus.DELAYED] * 1
        )
        sources = [OrderSource.CSV, OrderSource.JSON, OrderSource.MANUAL]

        orders = []
        for i in range(60):
            status = random.choice(statuses)
            vehicle = random.choice(vehicles) if status != OrderStatus.UNASSIGNED else None
            orders.append(
                Order(
                    customer_name=random.choice(CUSTOMER_NAMES),
                    phone_number=f"+91{random.randint(7000000000, 9999999999)}",
                    address=f"{random.choice(ADDRESSES)}, Bengaluru",
                    latitude=BASE_LAT + random_offset(),
                    longitude=BASE_LNG + random_offset(),
                    priority=random.choice(priorities),
                    time_window_start=f"{random.randint(8, 14):02d}:00",
                    time_window_end=f"{random.randint(15, 20):02d}:00",
                    package_weight=round(random.uniform(0.5, 15), 1),
                    special_instructions=random.choice(
                        [None, "Leave at door", "Call before delivery", "Fragile", None, None]
                    ),
                    status=status,
                    assigned_vehicle_id=vehicle.id if vehicle else None,
                    assigned_rider_id=vehicle.driver_user_id if vehicle else None,
                    created_via=random.choice(sources),
                )
            )
        db.add_all(orders)
        db.commit()

        print("Seeding rider performance...")
        performances = []
        for r in riders:
            performances.append(
                RiderPerformance(
                    rider_id=r.id,
                    deliveries_completed=random.randint(20, 150),
                    on_time_percentage=round(random.uniform(80, 99), 1),
                    average_delay=round(random.uniform(1, 15), 1),
                    route_adherence=round(random.uniform(85, 99), 1),
                    efficiency_score=round(random.uniform(70, 98), 1),
                    fuel_efficiency=round(random.uniform(75, 95), 1),
                )
            )
        db.add_all(performances)
        db.commit()

        print("Seeding route history...")
        history_rows = []
        for _ in range(40):
            v = random.choice(vehicles)
            eta_pred = round(random.uniform(15, 90), 1)
            delay = round(random.uniform(-5, 20), 1)
            history_rows.append(
                RouteHistory(
                    vehicle_id=v.id,
                    route=[
                        {"lat": BASE_LAT + random_offset(), "lng": BASE_LNG + random_offset()}
                        for _ in range(random.randint(3, 8))
                    ],
                    distance=round(random.uniform(5, 40), 2),
                    eta_predicted=eta_pred,
                    eta_actual=round(eta_pred + delay, 1),
                    traffic_mode=random.choice(list(TrafficMode)),
                    delay=max(delay, 0),
                    fuel_consumption=round(random.uniform(1, 8), 2),
                    co2_emissions=round(random.uniform(3, 20), 2),
                )
            )
        db.add_all(history_rows)
        db.commit()

        print("Seeding emission reports...")
        emission_rows = []
        for v in vehicles:
            fuel = round(random.uniform(10, 40), 2)
            optimized_fuel = round(fuel * random.uniform(0.7, 0.9), 2)
            emission_factor = 2.68
            emission_rows.append(
                EmissionReport(
                    vehicle_id=v.id,
                    distance=round(random.uniform(30, 150), 2),
                    fuel_used=fuel,
                    emission_factor=emission_factor,
                    co2_emissions=round(fuel * emission_factor, 2),
                    optimized_fuel=optimized_fuel,
                    fuel_savings=round(fuel - optimized_fuel, 2),
                    co2_savings=round((fuel - optimized_fuel) * emission_factor, 2),
                )
            )
        db.add_all(emission_rows)
        db.commit()

        print("Seeding hardware events...")
        hw_events = []
        demo_vehicle = vehicles[1]  # Van-02, matches the spec's demo flow
        hw_events.append(
            HardwareEvent(
                vehicle_id=demo_vehicle.id,
                event_type=HardwareEventType.BLOCK_DETECTED,
                latitude=BASE_LAT + random_offset(),
                longitude=BASE_LNG + random_offset(),
                previous_route=[{"lat": BASE_LAT, "lng": BASE_LNG}],
                new_route=None,
                status=HardwareEventStatus.RESOLVED,
            )
        )
        hw_events.append(
            HardwareEvent(
                vehicle_id=demo_vehicle.id,
                event_type=HardwareEventType.BLOCK_CLEARED,
                latitude=BASE_LAT + random_offset(),
                longitude=BASE_LNG + random_offset(),
                previous_route=None,
                new_route=[{"lat": BASE_LAT + 0.01, "lng": BASE_LNG + 0.01}],
                status=HardwareEventStatus.RESOLVED,
            )
        )
        db.add_all(hw_events)
        db.commit()

        print("Training initial ETA prediction model on seeded route history...")
        train_result = eta_model.train(db)
        print(f"  {train_result}")

        print("\nSeed complete.")
        print("=" * 50)
        print("Demo credentials:")
        print("  Admin:      admin@routexai.com / Admin@123")
        print("  Dispatcher: dispatcher@routexai.com / Dispatch@123")
        print("  Rider:      rider1@routexai.com / Rider@123  (also rider2..rider5)")
        print("=" * 50)

    finally:
        db.close()


if __name__ == "__main__":
    seed()
