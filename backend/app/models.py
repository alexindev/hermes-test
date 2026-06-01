from sqlalchemy import Column, String, Integer, Numeric, ForeignKey, DateTime, Enum as SAEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class OrderStatus(str, enum.Enum):
    created = "created"
    processing = "processing"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


class Seller(Base):
    __tablename__ = "sellers"

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)

    stores = relationship("Store", back_populates="seller")
    rating = relationship("SellerRating", back_populates="seller", uselist=False)


class Store(Base):
    __tablename__ = "stores"

    id = Column(UUID(as_uuid=True), primary_key=True)
    seller_id = Column(UUID(as_uuid=True), ForeignKey("sellers.id"))
    name = Column(String, nullable=False)

    seller = relationship("Seller", back_populates="stores")
    products = relationship("Product", back_populates="store")


class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"))
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))
    name = Column(String, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0)

    store = relationship("Store", back_populates="products")
    category = relationship("Category", back_populates="products")
    reviews = relationship("Review", back_populates="product")


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String, nullable=False, unique=True)
    full_name = Column(String)
    region = Column(String)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(SAEnum(OrderStatus), default=OrderStatus.created)
    total_amount = Column(Numeric(10, 2))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class OrderProduct(Base):
    __tablename__ = "orders_products"

    id = Column(UUID(as_uuid=True), primary_key=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2))


class Review(Base):
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    rating = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    product = relationship("Product", back_populates="reviews")


class SellerRating(Base):
    __tablename__ = "seller_ratings"

    id = Column(UUID(as_uuid=True), primary_key=True)
    seller_id = Column(UUID(as_uuid=True), ForeignKey("sellers.id"), unique=True)
    rating = Column(Integer)
    review_count = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    seller = relationship("Seller", back_populates="rating")


class Basket(Base):
    __tablename__ = "baskets"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False, default=1)
    added_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class Wishlist(Base):
    __tablename__ = "wishlists"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    added_at = Column(DateTime(timezone=True), default=datetime.utcnow)
