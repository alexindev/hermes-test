# Hermes Market — Open Marketplace

Открытый маркетплейс. Backend на FastAPI + SQLAlchemy, Frontend на React + Vite + TypeScript.

## 📋 О проекте

Веб-морда для существующей PostgreSQL базы данных маркетплейса. Read-only API.

### Стек

- **Backend:** Python 3.12, FastAPI, SQLAlchemy (async), asyncpg
- **Frontend:** React 18, TypeScript, Vite, React Router
- **База:** PostgreSQL 16

### API Endpoints

| Endpoint | Описание |
|----------|----------|
| `GET /api/products` | Список товаров (пагинация, фильтры, сортировка) |
| `GET /api/products/:id` | Детали товара + отзывы |
| `GET /api/categories` | Категории с количеством товаров |
| `GET /api/stores` | Магазины |
| `GET /api/sellers` | Продавцы с рейтингом |
| `GET /api/health` | Health check |

## 🚀 Запуск

### Локально (без Docker)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev  # http://localhost:5173
```

### Через Docker Compose
```bash
docker compose up -d
# Frontend: http://localhost:5173
# Backend:  http://localhost:8000/docs
```

## 🔧 Переменные окружения

Backend читает `DATABASE_URL` из переменной окружения. По умолчанию:
```
postgresql+asyncpg://postgres:@host.docker.internal:6432/bigdata
```

## 📁 Структура

```
backend/
├── app/
│   ├── main.py           # FastAPI приложение
│   ├── database.py       # Подключение к БД
│   ├── models.py         # SQLAlchemy модели
│   └── routers/
│       ├── products.py   # /api/products
│       ├── categories.py # /api/categories
│       ├── stores.py     # /api/stores
│       └── sellers.py    # /api/sellers
├── requirements.txt
└── Dockerfile

frontend/
├── src/
│   ├── App.tsx
│   ├── App.css
│   ├── api/client.ts     # API клиент
│   ├── components/
│   │   ├── Header.tsx
│   │   └── ProductCard.tsx
│   └── pages/
│       ├── CatalogPage.tsx
│       ├── ProductPage.tsx
│       └── SellersPage.tsx
├── package.json
├── vite.config.ts
└── Dockerfile

docker-compose.yml
```