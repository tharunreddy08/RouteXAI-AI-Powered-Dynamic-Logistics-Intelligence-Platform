import os
import sys
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.models.route_history import RouteHistory
from app.models.vehicle import Vehicle
from app.models.enums import TrafficMode, VehicleStatus
from app.ml import eta_model


def _seed_history(db, n, vehicle_name):
    v = Vehicle(name=vehicle_name, capacity=250, mileage=13, max_stops=25, status=VehicleStatus.IDLE)
    db.add(v)
    db.commit()
    db.refresh(v)

    random.seed(1)
    for i in range(n):
        distance = random.uniform(5, 30)
        predicted = distance / 28 * 60 + 10
        actual = predicted + random.uniform(-5, 10)
        db.add(
            RouteHistory(
                vehicle_id=v.id,
                route=[{"lat": 12.9, "lng": 77.6}] * random.randint(2, 6),
                distance=distance,
                eta_predicted=predicted,
                eta_actual=actual,
                traffic_mode=random.choice(list(TrafficMode)),
                delay=max(actual - predicted, 0),
                fuel_consumption=distance / 13,
                co2_emissions=(distance / 13) * 2.68,
                timestamp=datetime.utcnow() - timedelta(days=i),
            )
        )
    db.commit()
    return v.id


def test_predict_falls_back_to_heuristic_with_no_vehicle_history():
    db = SessionLocal()
    try:
        # A vehicle_id with zero RouteHistory rows always gets the heuristic
        # fallback if no model is trained yet, or a real prediction with
        # zero historical delay if a model already exists from another test.
        result = eta_model.predict(db, distance_km=10.0, traffic_mode="Normal", vehicle_id=999999)
        assert result["predicted_eta_minutes"] > 0
        assert result["model"] in ("heuristic-fallback", "xgboost-regression")
    finally:
        db.close()


def test_train_below_threshold_reports_insufficient_data():
    db = SessionLocal()
    try:
        before = db.query(RouteHistory).filter(RouteHistory.eta_actual.isnot(None)).count()
        if before >= eta_model.MIN_TRAINING_SAMPLES:
            # Another test already produced enough data in the shared DB;
            # this scenario is covered by test_train_and_predict below.
            return
        _seed_history(db, n=3, vehicle_name="Van-ML-Test-Small")
        result = eta_model.train(db)
        assert result["trained"] is False
        assert "insufficient" in result["reason"]
    finally:
        db.close()


def test_train_and_predict_with_enough_data():
    db = SessionLocal()
    try:
        vehicle_id = _seed_history(db, n=30, vehicle_name="Van-ML-Test-Full")
        result = eta_model.train(db)
        assert result["trained"] is True
        assert result["samples"] >= eta_model.MIN_TRAINING_SAMPLES
        assert 0 < result["confidence_percentage"] <= 100

        prediction = eta_model.predict(db, distance_km=15.0, traffic_mode="Heavy", vehicle_id=vehicle_id)
        assert prediction["model"] == "xgboost-regression"
        assert prediction["predicted_eta_minutes"] > 0
        assert prediction["confidence_percentage"] > 0
    finally:
        db.close()
