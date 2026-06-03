from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Order

router = APIRouter()


@router.get("/")
def list_orders(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Max number of records to return"),
):
    orders = (
        db.query(Order)
        .order_by(Order.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": str(o.id),
            "user_id": str(o.user_id) if o.user_id else None,
            "status": o.status,
            "total_amount": str(o.total_amount) if o.total_amount else None,
        }
        for o in orders
    ]
