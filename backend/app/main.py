from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import products, categories, stores, sellers

app = FastAPI(
    title="Hermes Market — Open Marketplace",
    description="API для открытого маркетплейса",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(stores.router, prefix="/api")
app.include_router(sellers.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "hermes-market"}