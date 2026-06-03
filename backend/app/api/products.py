from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product, Category, Seller, Store

router = APIRouter()


@router.get("/")
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
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
def list_categories(db: Session = Depends(get_db)):
    cats = db.query(Category).all()
    return [{"id": str(c.id), "name": c.name} for c in cats]


@router.get("/sellers")
def list_sellers(db: Session = Depends(get_db)):
    sellers = db.query(Seller).all()
    return [{"id": str(s.id), "name": s.name, "email": s.email} for s in sellers]


@router.get("/stores")
def list_stores(db: Session = Depends(get_db)):
    stores = db.query(Store).all()
    return [{"id": str(s.id), "seller_id": str(s.seller_id), "name": s.name} for s in stores]
