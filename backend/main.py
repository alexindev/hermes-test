"""FastAPI backend for hermes-test marketplace."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:@postgres:5432/bigdata")
engine = create_engine(DATABASE_URL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Verify DB connection on startup."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(f"✅ Database connected: {result.fetchone()}")
    yield
    print("🔌 Database connection closed")


app = FastAPI(
    title="Hermes Test API",
    description="Simple marketplace API backed by PostgreSQL",
    version="0.1.0",
    lifespan=lifespan,
)


# --- Pydantic models ---

class User(BaseModel):
    id: str
    email: str
    full_name: str
    region: str
    created_at: str


class Order(BaseModel):
    id: str
    user_id: str
    status: str
    total_amount: float
    created_at: str


class Product(BaseModel):
    id: str
    name: str
    price: float
    stock: int


class Category(BaseModel):
    id: str
    name: str


# --- Endpoints ---

@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/api/users", response_model=list[User])
def get_users(limit: int = 20):
    """Get users from the database."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id, email, full_name, region, created_at::text FROM users ORDER BY created_at DESC LIMIT :limit"),
            {"limit": limit},
        )
        rows = result.fetchall()
        return [
            User(
                id=str(r[0]),
                email=r[1],
                full_name=r[2],
                region=r[3],
                created_at=r[4],
            )
            for r in rows
        ]


@app.get("/api/orders", response_model=list[Order])
def get_orders(limit: int = 20):
    """Get recent orders."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id, user_id, status, total_amount, created_at::text FROM orders ORDER BY created_at DESC LIMIT :limit"),
            {"limit": limit},
        )
        rows = result.fetchall()
        return [
            Order(
                id=str(r[0]),
                user_id=str(r[1]),
                status=r[2],
                total_amount=float(r[3]),
                created_at=r[4],
            )
            for r in rows
        ]


@app.get("/api/products", response_model=list[Product])
def get_products(limit: int = 20):
    """Get products."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id, name, price, stock FROM products ORDER BY id LIMIT :limit"),
            {"limit": limit},
        )
        rows = result.fetchall()
        return [
            Product(
                id=str(r[0]),
                name=r[1],
                price=float(r[2]),
                stock=r[3],
            )
            for r in rows
        ]


@app.get("/api/categories", response_model=list[Category])
def get_categories():
    """Get all categories."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id, name FROM categories ORDER BY name"),
        )
        rows = result.fetchall()
        return [
            Category(id=str(r[0]), name=r[1])
            for r in rows
        ]


@app.get("/api/stats")
def get_stats():
    """Get simple stats from the database."""
    with engine.connect() as conn:
        users = conn.execute(text("SELECT count(*) FROM users")).scalar()
        orders = conn.execute(text("SELECT count(*) FROM orders")).scalar()
        products = conn.execute(text("SELECT count(*) FROM products")).scalar()
        categories = conn.execute(text("SELECT count(*) FROM categories")).scalar()
        return {
            "users": users,
            "orders": orders,
            "products": products,
            "categories": categories,
        }
