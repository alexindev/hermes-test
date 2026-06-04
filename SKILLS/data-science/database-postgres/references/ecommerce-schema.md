# E-commerce Database Schema (bigdata)

Source: session 2026-05-29. Self-hosted PostgreSQL on host.docker.internal:6432, DB bigdata.

## Tables and Row Counts

| Table | Rows | Purpose |
|-------|------|---------|
| categories | 20 | Product categories |
| sellers | 100 | Sellers (id, name, email) |
| seller_ratings | 100 | Seller ratings |
| stores | 191 | Stores (id, seller_id, name) |
| users | 1,000 | Buyers |
| products | 2,386 | Products (id, store_id, category_id, name, price, stock) |
| baskets | 4,031 | Shopping carts |
| wishlists | 7,386 | Wish lists |
| orders | 51,132 | Orders |
| reviews | 71,629 | Reviews (id, product_id, user_id, rating, created_at) |
| orders_products | 306,872 | Order line items |
| Total | 444,656 | |

## Categories (20)

Автотовары, Аксессуары и сумки, Бытовая химия, Детские товары, Дом и сад, Зоотовары, Игровые консоли, Канцелярия, Книги, Компьютеры и ноутбуки, Красота и здоровье, Мебель, Одежда и обувь, Парфюмерия, Продукты питания, Смартфоны и аксессуары, Спорттовары, Телевизоры и аудио, Фото и видео, Электроника

## Key Indexes

- idx_orders_user -> orders.user_id
- idx_products_store -> products.store_id
- idx_reviews_product -> reviews.product_id
- idx_baskets_user/product -> baskets.user_id, baskets.product_id
- idx_wishlists_user/product -> wishlists.user_id, wishlists.product_id
- Unique: sellers.email, users.email

## Common JOIN Paths

Revenue: sellers -> stores -> products -> orders_products -> orders
Rating: sellers -> stores -> products -> reviews
Basket: users -> baskets -> products