from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.database import Base, engine
from app.schemas import ProductOut, CategoryOut, SellerOut, StoreOut, UserOut, OrderOut
from app import api

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Marketplace API", version="0.1.0")

app.include_router(api.products, prefix="/api/products", tags=["products"])
app.include_router(api.categories, prefix="/api/categories", tags=["categories"])
app.include_router(api.sellers, prefix="/api/sellers", tags=["sellers"])
app.include_router(api.stores, prefix="/api/stores", tags=["stores"])
app.include_router(api.users, prefix="/api/users", tags=["users"])
app.include_router(api.orders, prefix="/api/orders", tags=["orders"])


@app.get("/api/health")
def health():
    return {"status": "ok"}
