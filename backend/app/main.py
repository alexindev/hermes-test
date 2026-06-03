from fastapi import FastAPI
from app.database import Base, engine
from app import api

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Marketplace API", version="0.1.0")

app.include_router(api.products, prefix="/api/products", tags=["products"])
app.include_router(api.users, prefix="/api/users", tags=["users"])
app.include_router(api.orders, prefix="/api/orders", tags=["orders"])


@app.get("/api/health")
def health():
    return {"status": "ok"}
