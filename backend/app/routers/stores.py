from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.models import Store, Seller, Product

router = APIRouter(tags=["stores"])


class StoreResponse(BaseModel):
    id: UUID
    name: str
    seller_name: Optional[str] = None
    product_count: int = 0

    class Config:
        from_attributes = True


@router.get("/stores", response_model=list[StoreResponse])
async def list_stores(db: AsyncSession = Depends(get_db)):
    query = (
        select(
            Store.id,
            Store.name,
            Seller.name.label("seller_name"),
            func.count(Product.id).label("product_count"),
        )
        .outerjoin(Seller, Store.seller_id == Seller.id)
        .outerjoin(Product, Product.store_id == Store.id)
        .group_by(Store.id, Seller.name)
        .order_by(Store.name)
    )
    result = await db.execute(query)
    return [
        StoreResponse(
            id=row.id,
            name=row.name,
            seller_name=row.seller_name,
            product_count=row.product_count,
        )
        for row in result.all()
    ]
