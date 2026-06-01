from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.models import Category, Product

router = APIRouter(tags=["categories"])


class CategoryResponse(BaseModel):
    id: UUID
    name: str
    product_count: int = 0

    class Config:
        from_attributes = True


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    query = (
        select(
            Category.id,
            Category.name,
            func.count(Product.id).label("product_count"),
        )
        .outerjoin(Product, Product.category_id == Category.id)
        .group_by(Category.id, Category.name)
        .order_by(Category.name)
    )
    result = await db.execute(query)
    return [
        CategoryResponse(id=row.id, name=row.name, product_count=row.product_count)
        for row in result.all()
    ]
