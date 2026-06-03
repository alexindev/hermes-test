from sqlalchemy import Column, Integer, Numeric, String, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    email = Column(String(255), nullable=False)
    full_name = Column(String(255))
    region = Column(String(100))
    created_at = Column(DateTime, server_default=text("now()"))


class Seller(Base):
    __tablename__ = "sellers"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)


class Store(Base):
    __tablename__ = "stores"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    seller_id = Column(UUID(as_uuid=True), ForeignKey("sellers.id"))
    name = Column(String(255), nullable=False)


class Category(Base):
    __tablename__ = "categories"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    name = Column(String(255), nullable=False)


class Product(Base):
    __tablename__ = "products"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"))
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))
    name = Column(String(255), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, server_default=text("0"))


class Order(Base):
    __tablename__ = "orders"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(String(50), nullable=False, server_default=text("'created'::order_status"))
    total_amount = Column(Numeric(12, 2))
    created_at = Column(DateTime, server_default=text("now()"))


class OrderProduct(Base):
    __tablename__ = "orders_products"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    quantity = Column(Integer, server_default=text("1"))
    unit_price = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(12, 2))


class Review(Base):
    __tablename__ = "reviews"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    rating = Column(Integer)
    created_at = Column(DateTime, server_default=text("now()"))


class SellerRating(Base):
    __tablename__ = "seller_ratings"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    seller_id = Column(UUID(as_uuid=True), ForeignKey("sellers.id"))
    rating = Column(Integer)
    review_count = Column(Integer, server_default=text("0"))
    updated_at = Column(DateTime, server_default=text("now()"))


class Basket(Base):
    __tablename__ = "baskets"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    quantity = Column(Integer, server_default=text("1"))
    added_at = Column(DateTime, server_default=text("now()"))


class Wishlist(Base):
    __tablename__ = "wishlists"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    added_at = Column(DateTime, server_default=text("now()"))
