# Marketplace Dashboard

Простой веб-интерфейс для работы с синтетическими данными маркетплейса (БД bigdata).

## Стек

- **Backend:** FastAPI + SQLAlchemy + PostgreSQL
- **Frontend:** React 19 + Vite + Nginx
- **Docker:** docker-compose для запуска

## Быстрый старт

```bash
# 1. Скопировать шаблон env
cp backend/.env.template backend/.env

# 2. Заполнить DATABASE_URL в backend/.env
#    Пример: DATABASE_URL=postgresql+psycopg2://postgres:password@host.docker.internal:6432/bigdata

# 3. Запустить
docker compose up --build
```

Открыть `http://localhost:3000` — фронтенд.
Swagger API: `http://localhost:8000/docs`

## Структура

```
├── backend/app/          # FastAPI приложение
│   ├── api/              # Роуты (products, orders, users)
│   ├── main.py           # Точка входа
│   ├── models.py         # SQLAlchemy модели (11 таблиц БД)
│   ├── schemas.py        # Pydantic схемы
│   └── database.py       # Подключение к БД
├── frontend/src/         # React приложение
│   ├── App.jsx           # Основной компонент
│   └── App.css           # Стили
├── docker-compose.yml
├── nginx.conf            # Конфиг nginx + проксирование
└── README.md
```

## API Endpoints

| Метод | Endpoint | Описание |
|-------|----------|-------------|
| GET | `/api/health` | Проверка здоровья |
| GET | `/api/products/` | Список товаров (пагинация: `?skip=0&limit=50`) |
| GET | `/api/products/categories` | Категории |
| GET | `/api/products/sellers` | Продавцы |
| GET | `/api/products/stores` | Магазины |
| GET | `/api/orders/` | Последние заказы (пагинация) |
| GET | `/api/users/` | Пользователи (пагинация) |

Все эндпоинты поддерживают пагинацию через `?skip=<offset>&limit=<count>` (max 200).

## Разработка

### Backend
```bash
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Docker
```bash
docker compose up --build -d
docker compose logs -f backend
docker compose logs -f frontend
```

## Деплой

Ветка `dev` → merge в `main`. CI/CD pipeline настраивается отдельно.
