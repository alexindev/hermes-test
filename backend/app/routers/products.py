from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from decimal import Decimal

from app.database import get_db
from app.models import Product, Category, Store, Seller, Review

router = APIRouter(tags=["products"])


class ProductResponse(BaseModel):
    id: UUID
    name: str
    price: Decimal
    stock: int
    store_name: Optional[str] = None
    category_name: Optional[str] = None
    avg_rating: Optional[float] = None
    review_count: int = 0

    class Config:
        from_attributes = True


class ProductDetail(BaseModel):
    id: UUID
    name: str
    price: Decimal
    stock: int
    store_name: Optional[str] = None
    seller_name: Optional[str] = None
    category_name: Optional[str] = None
    avg_rating: Optional[float] = None
    review_count: int = 0
    reviews: list = []

    class Config:
        from_attributes = True


@router.get("/products", response_model=list[ProductResponse])
async def list_products(
    category_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    min_price: Optional[Decimal] = Query(None),
    max_price: Optional[Decimal] = Query(None),
    sort: Optional[str] = Query("name"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(
            Product.id,
            Product.name,
            Product.price,
            Product.stock,
            Store.name.label("store_name"),
            Category.name.label("category_name"),
            func.coalesce(func.round(func.avg(Review.rating), 1), 0).label("avg_rating"),
            func.count(Review.id).label("review_count"),
        )
        .outerjoin(Store, Product.store_id == Store.id)
        .outerjoin(Category, Product.category_id == Category.id)
        .outerjoin(Review, Review.product_id == Product.id)
        .group_by(Product.id, Store.name, Category.name)
    )

    if category_id:
        query = query.where(Product.category_id == category_id)
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
    if min_price:
        query = query.where(Product.price >= min_price)
    if max_price:
        query = query.where(Product.price <= max_price)

    if sort == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())
    elif sort == "rating":
        query = query.order_by(func.avg(Review.rating).desc().nullslast())
    elif sort == "popular":
        query = query.order_by(func.count(Review.id).desc())
    else:
        query = query.order_by(Product.name.asc())

    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    rows = result.all()

    return [
        ProductResponse(
            id=row.id,
            name=row.name,
            price=row.price,
            stock=row.stock,
            store_name=row.store_name,
            category_name=row.category_name,
            avg_rating=float(row.avg_rating) if row.avg_rating else None,
            review_count=row.review_count,
        )
        for row in rows
    ]


@router.get("/products/{product_id}", response_model=ProductDetail)
async def get_product(product_id: UUID, db: AsyncSession = Depends(get_db)):
    query = (
        select(
            Product.id,
            Product.name,
            Product.price,
            Product.stock,
            Store.name.label("store_name"),
            Seller.name.label("seller_name"),
            Category.name.label("category_name"),
            func.coalesce(func.round(func.avg(Review.rating), 1), 0).label("avg_rating"),
            func.count(Review.id).label("review_count"),
        )
        .outerjoin(Store, Product.store_id == Store.id)
        .outerjoin(Seller, Store.seller_id == Seller.id)
        .outerjoin(Category, Product.category_id == Category.id)
        .outerjoin(Review, Review.product_id == Product.id)
        .where(Product.id == product_id)
        .group_by(Product.id, Store.name, Seller.name, Category.name)
    )
    result = await db.execute(query)
    row = result.one_or_none()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Product not found")

    rev_query = select(Review).where(Review.product_id == product_id).order_by(Review.created_at.desc()).limit(10)
    rev_result = await db.execute(rev_query)
    reviews = rev_result.scalars().all()

    return ProductDetail(
        id=row.id,
        name=row.name,
        price=row.price,
        stock=row.stock,
        store_name=row.store_name,
        seller_name=row.seller_name,
        category_name=row.category_name,
        avg_rating=float(row.avg_rating) if row.avg_rating else None,
        review_count=row.review_count,
        reviews=[
            {
                "id": str(r.id),
                "rating": r.rating,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reviews
        ],
    )
