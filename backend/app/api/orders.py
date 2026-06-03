from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Order

router = APIRouter()


@router.get("/")
def list_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).order_by(Order.created_at.desc()).limit(50).all()
    return [
        {
            "id": str(o.id),
            "user_id": str(o.user_id) if o.user_id else None,
            "status": o.status,
            "total_amount": str(o.total_amount) if o.total_amount else None,
        }
        for o in orders
    ]
