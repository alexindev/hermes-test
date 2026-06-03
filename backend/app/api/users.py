from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User

router = APIRouter()


@router.get("/")
def list_users(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Max number of records to return"),
):
    users = db.query(User).offset(skip).limit(limit).all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "full_name": u.full_name,
            "region": u.region,
        }
        for u in users
    ]
