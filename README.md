# Hermes Test

Simple web project: **FastAPI** (backend) + **React** (frontend) + **PostgreSQL 18** (database).

## Quick Start

```bash
# Copy env template
cp .env.template .env

# Build & run
docker compose up --build

# Open in browser
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

## Stack

| Component | Technology | Port |
|-----------|------------|------|
| Frontend  | React + Vite + Nginx | 3000 |
| Backend   | FastAPI + SQLAlchemy | 8000 |
| Database  | PostgreSQL 18 | 5432 |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/stats` | DB stats (users, orders, products count) |
| GET | `/api/users?limit=20` | List users |
| GET | `/api/orders?limit=20` | List orders |
| GET | `/api/products?limit=20` | List products |
| GET | `/api/categories` | List categories |

## Development

```bash
# Run only backend locally
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Run frontend dev server
cd frontend
npm install
npm run dev
```
