from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.models import Seller, Store, Product, SellerRating

router = APIRouter(tags=["sellers"])


class SellerResponse(BaseModel):
    id: UUID
    name: str
    email: str
    store_count: int = 0
    product_count: int = 0
    rating: Optional[float] = None
    review_count: int = 0

    class Config:
        from_attributes = True


@router.get("/sellers", response_model=list[SellerResponse])
async def list_sellers(db: AsyncSession = Depends(get_db)):
    query = (
        select(
            Seller.id,
            Seller.name,
            Seller.email,
            func.count(func.distinct(Store.id)).label("store_count"),
            func.count(func.distinct(Product.id)).label("product_count"),
            SellerRating.rating,
            SellerRating.review_count,
        )
        .outerjoin(Store, Store.seller_id == Seller.id)
        .outerjoin(Product, Product.store_id == Store.id)
        .outerjoin(SellerRating, SellerRating.seller_id == Seller.id)
        .group_by(Seller.id, SellerRating.rating, SellerRating.review_count)
        .order_by(Seller.name)
    )
    result = await db.execute(query)
    return [
        SellerResponse(
            id=row.id,
            name=row.name,
            email=row.email,
            store_count=row.store_count,
            product_count=row.product_count,
            rating=float(row.rating) if row.rating else None,
            review_count=row.review_count,
        )
        for row in result.all()
    ]


@router.get("/sellers/{seller_id}", response_model=SellerResponse)
async def get_seller(seller_id: UUID, db: AsyncSession = Depends(get_db)):
    from fastapi import HTTPException

    query = (
        select(
            Seller.id,
            Seller.name,
            Seller.email,
            func.count(func.distinct(Store.id)).label("store_count"),
            func.count(func.distinct(Product.id)).label("product_count"),
            SellerRating.rating,
            SellerRating.review_count,
        )
        .outerjoin(Store, Store.seller_id == Seller.id)
        .outerjoin(Product, Product.store_id == Store.id)
        .outerjoin(SellerRating, SellerRating.seller_id == Seller.id)
        .where(Seller.id == seller_id)
        .group_by(Seller.id, SellerRating.rating, SellerRating.review_count)
    )
    result = await db.execute(query)
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Seller not found")
    return SellerResponse(
        id=row.id,
        name=row.name,
        email=row.email,
        store_count=row.store_count,
        product_count=row.product_count,
        rating=float(row.rating) if row.rating else None,
        review_count=row.review_count,
    )
