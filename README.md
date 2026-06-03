# Marketplace Dashboard

Простой веб-интерфейс для работы с синтетическими данными маркетплейса (БД bigdata).

## Стек

- **Backend:** FastAPI + SQLAlchemy + PostgreSQL
- **Frontend:** React 19 + Vite + Nginx
- **Docker:** docker-compose для запуска

## Запуск

```bash
# Backend (FastAPI)
cd backend
pip install -e .
uvicorn app.main:app --reload --port 8000

# Frontend (React)
cd frontend
npm install
npm run dev
```

## API

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/health` | Проверка здоровья |
| GET | `/api/products/` | Список товаров |
| GET | `/api/products/categories` | Категории |
| GET | `/api/products/sellers` | Продавцы |
| GET | `/api/products/stores` | Магазины |
| GET | `/api/orders/` | Последние заказы |
| GET | `/api/users/` | Пользователи |

## Структура

```
├── backend/app/          # FastAPI приложение
│   ├── api/              # Роуты
│   ├── main.py           # Точка входа
│   ├── models.py         # SQLAlchemy модели
│   ├── schemas.py        # Pydantic схемы
│   └── database.py       # Подключение к БД
├── frontend/src/         # React приложение
├── docker-compose.yml
└── README.md
```

## Деплой

Ветка `dev` → основной репозиторий.
