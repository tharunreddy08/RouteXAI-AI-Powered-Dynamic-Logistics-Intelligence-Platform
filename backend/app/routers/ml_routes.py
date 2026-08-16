from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.route_history import RouteHistory
from app.models.enums import OrderStatus
from app.schemas.route_history import (
    RouteHistoryOut,
    RouteHistoryCreate,
    ETAPredictionResponse,
)
from app.utils.deps import get_current_user, require_dispatcher
from app.ml import eta_model

router = APIRouter(tags=["ML & Route History"])


@router.get("/route-history", response_model=List[RouteHistoryOut])
def list_route_history(
    limit: int = Query(default=200, le=1000),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return (
        db.query(RouteHistory)
        .order_by(RouteHistory.timestamp.desc())
        .limit(limit)
        .all()
    )


@router.post("/route-history", response_model=RouteHistoryOut, status_code=201)
def record_route_history(
    payload: RouteHistoryCreate,
    db: Session = Depends(get_db),
    _=Depends(require_dispatcher),
):
    """
    Records a completed delivery's actual outcome. This is the trigger point
    for the self-learning feedback loop described in spec section 13:
    Route Created -> ETA Predicted -> Delivery Completed -> Actual ETA
    Recorded -> Prediction Error Calculated -> RouteHistory Updated ->
    Model Retrained -> Improved Future ETA.

    Retraining runs synchronously here for demo transparency; in a
    production deployment this would be offloaded to a background worker.
    """
    delay = 0.0
    if payload.eta_predicted is not None:
        delay = max(payload.eta_actual - payload.eta_predicted, 0.0)

    history = RouteHistory(
        vehicle_id=payload.vehicle_id,
        route=payload.route,
        distance=payload.distance,
        eta_predicted=payload.eta_predicted,
        eta_actual=payload.eta_actual,
        traffic_mode=payload.traffic_mode,
        delay=delay,
        fuel_consumption=payload.fuel_consumption,
        co2_emissions=payload.co2_emissions,
    )
    db.add(history)
    db.commit()
    db.refresh(history)

    # Batch retrain (see eta_model.train docstring for what this does and
    # does not claim about "learning").
    eta_model.train(db)

    return history


@router.get("/ml/eta", response_model=ETAPredictionResponse)
def predict_eta(
    distance_km: float = Query(..., gt=0),
    traffic_mode: str = Query(default="Normal"),
    vehicle_id: int | None = Query(default=None),
    num_stops: int = Query(default=1, ge=1),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    result = eta_model.predict(
        db,
        distance_km=distance_km,
        traffic_mode=traffic_mode,
        vehicle_id=vehicle_id,
        num_stops=num_stops,
    )
    return ETAPredictionResponse(**result)


@router.get("/ml/status")
def ml_status(db: Session = Depends(get_db), _=Depends(get_current_user)):
    """Non-spec convenience endpoint: current model state for the ML Insights
    panel planned in Phase 6, and for debugging the feedback loop."""
    model, metadata = eta_model._load_model()
    history_count = db.query(RouteHistory).filter(RouteHistory.eta_actual.isnot(None)).count()
    return {
        "model_trained": model is not None,
        "training_samples_available": history_count,
        "min_samples_required": eta_model.MIN_TRAINING_SAMPLES,
        "metadata": metadata or {},
        "optimization_engine": "Google OR-Tools (VRPTW)",
        "shortest_path_algorithm": "A* Search",
        "eta_prediction_model": "Supervised Regression (XGBoost)",
    }
