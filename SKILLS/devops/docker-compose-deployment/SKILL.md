---
name: docker-compose-deployment
description: Развёртывание проектов через Docker Compose на удалённом сервере. Workflow PR → main, сборка, запуск, troubleshooting портов и build-ошибок.
---

# docker-compose-deployment

Развёртывание проектов через Docker Compose на удалённом сервере (VM).

## Workflow

1. Локально: создать ветку (`fix/...` или `dev/...`) → коммит → пуш
2. Создать PR → пользователь апрувит и мержит в `main`
3. На сервере: `git checkout main && git pull origin main`
4. Пересобрать: `sudo docker compose up -d --build`
5. Проверить: `sudo docker compose ps`, `sudo docker compose logs`

## Pitfalls

### Port conflict — порт уже занят

Если `Bind for 0.0.0.0:PORT failed: port is already allocated`:
- Найти занявший порт: `sudo ss -tlnp | grep :PORT`
- Если это контейнер — остановить: `sudo docker stop <container>`
- Если это хост-процесс (nginx, uvicorn) — убить: `sudo kill -9 <PID>`
- Либо переназначить порт в docker-compose.yml

### Host PostgreSQL вместо container PostgreSQL

Когда БД уже запущена на хосте (не в compose):
- Убрать сервис `postgres` из docker-compose.yml
- Добавить `extra_hosts: ["host.docker.internal:host-gateway"]` для backend
- Обновить `DATABASE_URL` в `.env` на `host.docker.internal:<port>`
- **НЕ коммитить** `.env` — он в `.gitignore`

### Build failures — setuptools / pip

- `setuptools.backends._legacy:_Backend` удалён в v70+. Использовать `setuptools.build_meta`
- Фиксировать версии в `pyproject.toml`: `requires = ["setuptools>=68,<70"]` если legacy нужен
- Перед `pip install` обновлять: `RUN pip install --upgrade pip setuptools wheel`

### IPv6 on VM

Docker Hub может резолвиться в IPv6, который недоступен на VM.
Решение: настроить Docker daemon для IPv4-only (если есть права на /etc/docker).

## Common code bugs (import / runtime errors)

### SQLAlchemy 2.x: `Timestamp` удалён
- `from sqlalchemy import Timestamp` → `ImportError`
- Заменить на `DateTime` (из `sqlalchemy import DateTime`)
- Найти и заменить: `sed -i 's/Timestamp/DateTime/g' models.py`

### FastAPI `include_router`: нужен `.router`, не модуль
- ❌ `app.include_router(api.products, ...)` — `AttributeError: no attribute 'routes'`
- ✅ `app.include_router(api.products.router, ...)`

### Пустой `__init__.py` в package
- Модули не импортируются автоматически
- Добавить: `from app.api import products, orders, users`

## Server-specific notes

### Docker требует sudo
- На сервере: `sudo docker compose ...`
- Без sudo: `permission denied while connecting to Docker API`

### SSH доступ
- Хост: `hermes@158.160.4.7`
- Ключ: `~/.ssh/id_ed25519` (не передаётся автоматически)
- Команда: `ssh -i ~/.ssh/id_ed25519 hermes@158.160.4.7 "..."`

### Nginx на хосте занимает порт 80
- Если `docker compose` падает с `address already in use` на порту 80
- Проверить: `sudo ss -tlnp | grep ':80 '`
- Решение: изменить маппинг в compose.yml на свободный порт (напр. 8080)

### Protected branch — push в main не работает
- `GH006: Protected branch update failed`
- Всегда через PR: `gh pr create` → мержит пользователь
- На сервере нет GitHub-кредов — пушить нельзя

### Прямой процесс вместо Docker
- uvicorn может быть запущен напрямую на хосте (pid из `ss -tlnp`)
- Убить: `sudo kill -9 <PID>` перед запуском docker compose

## Environment files

- `.env.template` — шаблон с верными кредями (коммитится, но без реальных секретов)
- `.env` — рабочий файл (игнорируется git)
- **НЕ создавать** `.env.example` — только `.env.template`

## Verification steps

После `docker compose up -d --build`:
1. `sudo docker compose ps` — все сервисы `Up`
2. `sudo docker compose logs backend` — нет ошибок подключения к БД
3. Проверить healthcheck: `curl http://localhost:8000/api/health`
4. Проверить фронтенд: `curl http://localhost:<port>`