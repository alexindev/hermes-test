---
name: docker-compose-web-project
description: "Create and deploy a full-stack web project using Docker Compose with host networking for external DB connectivity."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [Docker, FastAPI, React, PostgreSQL, Deployment, Workflow]
    related_skills: [local-to-vm-deploy, github-pr-workflow, docker-browserless-setup]
---

# Docker Compose Web Project

Create and deploy a full-stack web project using Docker Compose with **host networking** for connecting to external services on the host machine (e.g., an external PostgreSQL container via `host.docker.internal`).

## When to use

When the user asks to create a web project with backend + frontend that runs in Docker Compose and needs to connect to services on the host machine. The database is NOT part of compose — it runs in a separate container.

## Core pattern

```
frontend (nginx:3000) → backend (fastapi:8000) → host.docker.internal:6432 (external PostgreSQL)
```

## Project structure

```
project/
├── docker-compose.yml    # services only, NO database service
├── .env.template         # secrets template (never commit .env)
├── .gitignore
├── README.md
├── backend/
│   ├── main.py           # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── main.jsx
    │   └── index.css
    ├── index.html
    ├── package.json
    ├── vite.config.js
    ├── nginx.conf          # proxy /api → backend
    └── Dockerfile
```

## Docker Compose config

Key rules:
- **NO database service** — use external DB
- **Use `network_mode: host`** so containers can reach `host.docker.internal`
- No custom Docker networks
- Frontend Nginx proxies `/api/*` calls to backend

```yaml
services:
  backend:
    build: ./backend
    restart: unless-stopped
    network_mode: host
    environment:
      DATABASE_URL: ${DATABASE_URI}

  frontend:
    build: ./frontend
    restart: unless-stopped
    network_mode: host
```

## .env.template

Always include the DATABASE_URI pointing to external DB:

```
DATABASE_URI=postgresql://user:pass@host.docker.internal:PORT/dbname
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

## Frontend nginx.conf

Proxy API calls to backend via localhost:

```nginx
server {
    listen 3000;
    location / {
        try_files $uri $uri/ /index.html;
    }
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }
}
```

## Backend Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Frontend Dockerfile (multi-stage)

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
ENV NODE_TLS_REJECT_UNAUTHORIZED=0
COPY package.json ./
RUN npm install --strict-ssl=false
COPY . .
RUN npm run build
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
```

## Testing workflow

### 1. Verify backend manually first

Before Docker, test the backend directly to catch DB connection issues:

```bash
cd backend
/opt/data/hermes-tools/.venv/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
# Test: curl http://localhost:8000/api/health
# Test: curl http://localhost:8000/api/stats
```

If pip is missing in venv, bootstrap it:
```bash
curl -sS https://bootstrap.pypa.io/get-pip.py | /opt/data/hermes-tools/.venv/bin/python3
```

### 2. Build and run with Docker Compose

```bash
cp .env.template .env
docker compose up -d --build
```

### 3. Verify containers are running

```bash
docker compose ps -a
docker compose logs backend  # check for DB connection errors
```

### 4. Git workflow

If branch has no common history with main:
```bash
git fetch origin main
git merge origin/main --allow-unrelated-histories -m "Merge branch 'main' into dev"
git push origin dev
gh pr create --base main --head dev --title "..." --body "..."
```

## ⚠️ Pitfalls

### Containers stuck in "Created" state
`docker compose start` may hang indefinitely. Use `docker start <container>` directly instead.

### npm install fails with SELF_SIGNED_CERT_IN_CHAIN
Two things needed:
1. Set `NODE_TLS_REJECT_UNAUTHORIZED=0` env var in Dockerfile
2. Use `--strict-ssl=false` flag on npm install command

Both are required — one alone is not enough.

### No pip in venv
The venv at `/opt/data/hermes-tools/.venv/` may lack pip. Bootstrap with:
```bash
curl -sS https://bootstrap.pypa.io/get-pip.py | /opt/data/hermes-tools/.venv/bin/python3
```

### Database in compose
User explicitly does NOT want a database container in compose. Connect to external DB via `host.docker.internal`.

### Custom Docker networks
Don't create custom networks. Use `network_mode: host` for host connectivity. This avoids DNS resolution issues with `host.docker.internal`.

### gh pr create fails with "no common history"
When creating a PR from a fresh branch, merge main first:
```bash
git merge origin/main --allow-unrelated-histories
git push origin dev
gh pr create --base main --head dev ...
```