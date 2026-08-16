from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.rider_performance import RiderPerformance
from app.models.user import User
from app.schemas.rider_performance import RiderPerformanceOut
from app.utils.deps import get_current_user

router = APIRouter(prefix="/riders", tags=["Riders"])


@router.get("/performance", response_model=List[RiderPerformanceOut])
def rider_performance(db: Session = Depends(get_db), _=Depends(get_current_user)):
    rows = (
        db.query(RiderPerformance, User)
        .join(User, RiderPerformance.rider_id == User.id)
        .order_by(RiderPerformance.efficiency_score.desc())
        .all()
    )
    return [
        RiderPerformanceOut(
            rider_id=perf.rider_id,
            rider_name=user.name,
            deliveries_completed=perf.deliveries_completed,
            on_time_percentage=perf.on_time_percentage,
            average_delay=perf.average_delay,
            route_adherence=perf.route_adherence,
            efficiency_score=perf.efficiency_score,
            fuel_efficiency=perf.fuel_efficiency,
            updated_at=perf.updated_at,
        )
        for perf, user in rows
    ]
