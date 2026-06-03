from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product, Category, Seller, Store

router = APIRouter()


@router.get("/")
def list_products(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Max number of records to return"),
):
    products = db.query(Product).offset(skip).limit(limit).all()
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "price": str(p.price),
            "stock": p.stock,
            "store_id": str(p.store_id) if p.store_id else None,
            "category_id": str(p.category_id) if p.category_id else None,
        }
        for p in products
    ]


@router.get("/categories")
def list_categories(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    cats = db.query(Category).offset(skip).limit(limit).all()
    return [{"id": str(c.id), "name": c.name} for c in cats]


@router.get("/sellers")
def list_sellers(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    sellers = db.query(Seller).offset(skip).limit(limit).all()
    return [{"id": str(s.id), "name": s.name, "email": s.email} for s in sellers]


@router.get("/stores")
def list_stores(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    stores = db.query(Store).offset(skip).limit(limit).all()
    return [{"id": str(s.id), "seller_id": str(s.seller_id), "name": s.name} for s in stores]
