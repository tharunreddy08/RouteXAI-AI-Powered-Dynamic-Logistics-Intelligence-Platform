"""
ML-based ETA prediction using XGBoost regression, trained on RouteHistory.

Honesty note (per spec section 13): this is **incremental batch retraining**,
not continuous online learning. Each time `train()` is called, it refits a
fresh model on the full accumulated RouteHistory table. This is a real,
measurable feedback loop (predictions improve as more delivery outcomes are
recorded) but it is not autonomous/continuous learning, and the API/UI
should not describe it as such.
"""
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any

import joblib
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from xgboost import XGBRegressor
from sqlalchemy.orm import Session

from app.models.route_history import RouteHistory
from app.ml.features import build_feature_vector, FEATURE_NAMES

logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
MODEL_PATH = os.path.join(MODEL_DIR, "eta_model.joblib")
METADATA_PATH = os.path.join(MODEL_DIR, "eta_model_meta.joblib")

MIN_TRAINING_SAMPLES = 15  # below this, fall back to a heuristic estimate

# Fallback heuristic constants (used until enough real history accumulates).
FALLBACK_SPEED_KMPH = 28.0
FALLBACK_SERVICE_MIN_PER_STOP = 5.0
FALLBACK_CONFIDENCE = 50.0  # explicitly lower than a trained model's confidence


def _vehicle_avg_delay(db: Session, vehicle_id: Optional[int]) -> float:
    if vehicle_id is None:
        return 0.0
    rows = (
        db.query(RouteHistory)
        .filter(RouteHistory.vehicle_id == vehicle_id)
        .order_by(RouteHistory.timestamp.desc())
        .limit(20)
        .all()
    )
    if not rows:
        return 0.0
    return sum(r.delay for r in rows) / len(rows)


def train(db: Session) -> Dict[str, Any]:
    """
    Retrain the ETA model on all RouteHistory rows that have both a
    predicted and an actual ETA recorded. Returns training metadata.
    """
    rows = (
        db.query(RouteHistory)
        .filter(RouteHistory.eta_actual.isnot(None))
        .all()
    )

    if len(rows) < MIN_TRAINING_SAMPLES:
        logger.info(
            "Only %d RouteHistory samples with actuals — need >= %d to train. Skipping.",
            len(rows),
            MIN_TRAINING_SAMPLES,
        )
        return {
            "trained": False,
            "reason": f"insufficient data ({len(rows)}/{MIN_TRAINING_SAMPLES} samples)",
            "samples": len(rows),
        }

    X, y = [], []
    for r in rows:
        num_stops = len(r.route) if isinstance(r.route, list) else 1
        avg_delay = _vehicle_avg_delay(db, r.vehicle_id)
        X.append(
            build_feature_vector(
                distance_km=r.distance,
                traffic_mode=r.traffic_mode.value if hasattr(r.traffic_mode, "value") else r.traffic_mode,
                timestamp=r.timestamp,
                num_stops=max(num_stops, 1),
                historical_avg_delay=avg_delay,
                vehicle_mileage=12.0,  # historical vehicle mileage isn't stored per-row; use fleet avg
            )
        )
        y.append(r.eta_actual)

    X = np.array(X)
    y = np.array(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = XGBRegressor(
        n_estimators=150,
        max_depth=4,
        learning_rate=0.08,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
        objective="reg:squarederror",
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = float(mean_absolute_error(y_test, preds))
    mean_actual = float(np.mean(y_test)) if len(y_test) else 1.0
    error_pct = (mae / mean_actual * 100) if mean_actual > 0 else 100.0
    confidence = max(40.0, min(97.0, 100 - error_pct))

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    metadata = {
        "trained_at": datetime.utcnow().isoformat(),
        "samples": len(rows),
        "mae_minutes": round(mae, 2),
        "confidence_percentage": round(confidence, 1),
        "feature_names": FEATURE_NAMES,
    }
    joblib.dump(metadata, METADATA_PATH)

    logger.info("ETA model retrained: %s", metadata)
    return {"trained": True, **metadata}


def _load_model():
    if not os.path.exists(MODEL_PATH):
        return None, None
    try:
        model = joblib.load(MODEL_PATH)
        metadata = joblib.load(METADATA_PATH) if os.path.exists(METADATA_PATH) else {}
        return model, metadata
    except Exception as e:  # pragma: no cover - defensive
        logger.warning("Failed to load ETA model: %s", e)
        return None, None


def predict(
    db: Session,
    distance_km: float,
    traffic_mode: str = "Normal",
    vehicle_id: Optional[int] = None,
    num_stops: int = 1,
    vehicle_mileage: float = 12.0,
) -> Dict[str, Any]:
    """
    Predict ETA (minutes) and a confidence percentage.

    Falls back to a transparent heuristic (clearly labeled as such) when no
    trained model exists yet or too little history has been recorded.
    """
    model, metadata = _load_model()
    avg_delay = _vehicle_avg_delay(db, vehicle_id)

    if model is None:
        base_minutes = (distance_km / FALLBACK_SPEED_KMPH) * 60
        service_minutes = num_stops * FALLBACK_SERVICE_MIN_PER_STOP
        traffic_penalty = {"Normal": 1.0, "Heavy": 1.4, "Accident": 1.7}.get(traffic_mode, 1.0)
        predicted = (base_minutes + service_minutes) * traffic_penalty + avg_delay
        return {
            "predicted_eta_minutes": round(predicted, 1),
            "expected_delay_minutes": round(avg_delay, 1),
            "confidence_percentage": FALLBACK_CONFIDENCE,
            "model": "heuristic-fallback",
            "note": "Trained model not yet available (insufficient RouteHistory samples); using a distance/traffic heuristic.",
        }

    features = np.array(
        [
            build_feature_vector(
                distance_km=distance_km,
                traffic_mode=traffic_mode,
                timestamp=datetime.utcnow(),
                num_stops=num_stops,
                historical_avg_delay=avg_delay,
                vehicle_mileage=vehicle_mileage,
            )
        ]
    )
    predicted = float(model.predict(features)[0])

    return {
        "predicted_eta_minutes": round(max(predicted, 1.0), 1),
        "expected_delay_minutes": round(avg_delay, 1),
        "confidence_percentage": metadata.get("confidence_percentage", 70.0),
        "model": "xgboost-regression",
        "model_trained_at": metadata.get("trained_at"),
        "model_mae_minutes": metadata.get("mae_minutes"),
    }
