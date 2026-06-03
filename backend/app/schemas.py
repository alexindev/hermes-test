from pydantic import BaseModel
from typing import Optional
from decimal import Decimal


class ProductOut(BaseModel):
    id: str
    name: str
    price: Decimal
    stock: int
    store_id: Optional[str] = None
    category_id: Optional[str] = None

    model_config = {"from_attributes": True}


class CategoryOut(BaseModel):
    id: str
    name: str

    model_config = {"from_attributes": True}


class SellerOut(BaseModel):
    id: str
    name: str
    email: str

    model_config = {"from_attributes": True}


class StoreOut(BaseModel):
    id: str
    seller_id: Optional[str] = None
    name: str

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    region: Optional[str] = None

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: str
    user_id: Optional[str] = None
    status: str
    total_amount: Optional[Decimal] = None

    model_config = {"from_attributes": True}
