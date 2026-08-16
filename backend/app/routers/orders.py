from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.order import Order
from app.models.enums import OrderStatus, OrderSource
from app.schemas.order import (
    OrderOut,
    OrderCreate,
    OrderUpdate,
    ManualOrderRequest,
    UploadResult,
)
from app.utils.deps import get_current_user, require_dispatcher
from app.services.order_ingestion import parse_csv, parse_json
from app.services.optimization_service import run_optimization

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=List[OrderOut])
def list_orders(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Order).order_by(Order.created_at.desc()).all()


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    return order


def _create_order(db: Session, payload: OrderCreate, created_via: OrderSource) -> Order:
    order = Order(
        customer_name=payload.customer_name,
        phone_number=payload.phone_number,
        address=payload.address,
        latitude=payload.latitude,
        longitude=payload.longitude,
        priority=payload.priority,
        time_window_start=payload.time_window_start,
        time_window_end=payload.time_window_end,
        package_weight=payload.package_weight,
        special_instructions=payload.special_instructions,
        status=OrderStatus.UNASSIGNED,
        created_via=created_via,
    )
    db.add(order)
    return order


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    _=Depends(require_dispatcher),
):
    """Generic order creation (used internally by manual entry / upload; also
    usable directly for programmatic integrations)."""
    order = _create_order(db, payload, OrderSource.MANUAL)
    db.commit()
    db.refresh(order)
    return order


@router.post("/manual", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_manual_order(
    payload: ManualOrderRequest,
    db: Session = Depends(get_db),
    _=Depends(require_dispatcher),
):
    """
    Manual Order Entry tab: 'Add Order' (optimize=False) or
    'Save & Optimize' (optimize=True), per spec section 7.
    """
    order = _create_order(db, payload.order, OrderSource.MANUAL)
    db.commit()
    db.refresh(order)

    if payload.optimize:
        run_optimization(db, order_ids=[order.id])
        db.refresh(order)

    return order


@router.post("/upload", response_model=UploadResult, status_code=status.HTTP_201_CREATED)
async def upload_orders(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(require_dispatcher),
):
    """CSV or JSON bulk order upload. Existing upload behavior is preserved:
    rows/items that fail validation are reported but don't block the rest."""
    content = await file.read()
    filename = (file.filename or "").lower()

    if filename.endswith(".csv"):
        rows, errors = parse_csv(content)
    elif filename.endswith(".json"):
        rows, errors = parse_json(content)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Upload a .csv or .json file.",
        )

    created_ids: List[int] = []
    source = OrderSource.CSV if filename.endswith(".csv") else OrderSource.JSON

    for row in rows:
        order = _create_order(db, row, source)
        db.flush()
        created_ids.append(order.id)

    db.commit()

    return UploadResult(
        created=len(created_ids),
        failed=len(errors),
        errors=errors,
        order_ids=created_ids,
    )


@router.put("/{order_id}", response_model=OrderOut)
def update_order(
    order_id: int,
    payload: OrderUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_dispatcher),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    data = payload.model_dump(exclude_unset=True)
    if "status" in data:
        # A manual status edit is protected from the 15-minute auto-sync job.
        order.status_manually_set = 1
    for field, value in data.items():
        setattr(order, field, value)

    db.commit()
    db.refresh(order)
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_dispatcher),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    db.delete(order)
    db.commit()
    return None
