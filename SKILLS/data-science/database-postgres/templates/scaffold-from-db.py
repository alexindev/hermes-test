#!/usr/bin/env python3
"""
Scaffold a FastAPI + React project from an existing PostgreSQL database.

Usage:
    python scaffold_from_db.py --host host.docker.internal --port 6432 --db bigdata --user postgres --output ./project-dir

Steps:
    1. Inspect all tables and columns via information_schema
    2. Generate SQLAlchemy models (models.py) with UUID primary keys
    3. Generate Pydantic schemas (schemas.py) for read responses
    4. Generate API routes (api/*.py) — list endpoints for each table
    5. Generate React frontend (frontend/src/App.jsx) with dashboard + tables
    6. Generate docker-compose.yml, Dockerfiles, README.md
    7. Git init → commit → push to dev branch

Output structure:
    project/
    ├── backend/app/
    │   ├── main.py          # FastAPI entrypoint
    │   ├── models.py        # SQLAlchemy ORM models
    │   ├── schemas.py       # Pydantic response schemas
    │   ├── database.py      # Engine + session factory
    │   ├── config.py        # Settings (DATABASE_URL from env)
    │   └── api/             # Route modules per entity
    ├── frontend/src/
    │   ├── App.jsx          # Dashboard with stats + tables
    │   └── main.jsx         # React entrypoint
    ├── docker-compose.yml
    ├── nginx.conf           # Reverse proxy /api → backend
    ├── README.md
    └── .gitignore
"""

import argparse
import os
import sys
from pathlib import Path


def inspect_tables(host, port, dbname, user):
    """Connect to DB and return table info."""
    try:
        import psycopg2
    except ImportError:
        print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary", file=sys.stderr)
        sys.exit(1)

    conn = psycopg2.connect(
        host=host, port=port, dbname=dbname, user=user
    )
    cur = conn.cursor()

    # Get all tables in public schema
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    tables = [r[0] for r in cur.fetchall()]

    table_info = {}
    for tbl in tables:
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default, ordinal_position
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position;
        """, (tbl,))
        cols = cur.fetchall()
        table_info[tbl] = {
            'columns': [
                {
                    'name': c[0],
                    'type': c[1],
                    'nullable': c[2] == 'YES',
                    'default': c[3],
                    'position': c[4],
                }
                for c in cols
            ]
        }

    cur.close()
    conn.close()
    return table_info


def generate_models(table_info, output_dir):
    """Generate SQLAlchemy models.py."""
    path = output_dir / "backend" / "app" / "models.py"
    lines = [
        "from sqlalchemy import Column, Integer, Numeric, String, Timestamp, ForeignKey, text",
        "from sqlalchemy.dialects.postgresql import UUID",
        "from app.database import Base",
        "import uuid",
        "",
        "",
    ]

    type_map = {
        'uuid': 'UUID(as_uuid=True)',
        'character varying': 'String(255)',
        'integer': 'Integer',
        'numeric': 'Numeric(10, 2)',
        'timestamp with time zone': 'Timestamp',
        'boolean': 'Boolean',
    }

    for tbl_name, tbl_data in sorted(table_info.items()):
        class_name = ''.join(w.capitalize() for w in tbl_name.split('_'))
        lines.append(f"class {class_name}(Base):")
        lines.append(f'    __tablename__ = "{tbl_name}"')
        lines.append("    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)")
        lines.append("")

        for col in tbl_data['columns']:
            if col['name'] == 'id':
                continue
            sa_type = type_map.get(col['type'], 'String(255)')
            nullable = "" if col['nullable'] else ", nullable=False"
            default = ""
            if col['default'] and col['default'] != 'NULL':
                if col['default'].startswith("'"):
                    default = f", default={col['default']}"
                elif 'now()' in str(col['default']):
                    default = f", server_default=text(\"{col['default']}\")"
                else:
                    default = f", default={col['default']}"
            fk = ""
            if 'id' in col['name'].lower() and col['name'] != 'id':
                ref_tbl = col['name'].replace('_id', '')
                fk = f", ForeignKey(\"{ref_tbl}.id\")"
            lines.append(f"    {col['name']} = Column({sa_type}{nullable}{fk}{default})")
        lines.append("")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines))
    print(f"  ✓ {path}")


def generate_schemas(table_info, output_dir):
    """Generate Pydantic schemas."""
    path = output_dir / "backend" / "app" / "schemas.py"
    lines = [
        "from pydantic import BaseModel",
        "from typing import Optional",
        "from decimal import Decimal",
        "",
        "",
    ]

    for tbl_name, tbl_data in table_info.items():
        class_name = ''.join(w.capitalize() for w in tbl_name.split('_'))
        out_name = f"{class_name}Out"
        lines.append(f"class {out_name}(BaseModel):")
        for col in tbl_data['columns']:
            if col['name'] == 'id':
                lines.append(f"    id: str")
            elif col['type'] == 'numeric':
                lines.append(f"    {col['name']}: Optional[Decimal] = None")
            elif col['nullable']:
                lines.append(f"    {col['name']}: Optional[str] = None")
            else:
                lines.append(f"    {col['name']}: str")
        lines.append('')
        lines.append('    model_config = {"from_attributes": True}')
        lines.append('')
        lines.append('')

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines))
    print(f"  ✓ {path}")


def generate_api_routes(table_info, output_dir):
    """Generate API route files."""
    api_dir = output_dir / "backend" / "app" / "api"
    api_dir.mkdir(parents=True, exist_ok=True)
    (api_dir / "__init__.py").write_text("")

    # Group tables into logical route files
    groups = {
        'products': ['products', 'categories', 'stores', 'sellers'],
        'orders': ['orders', 'orders_products'],
        'users': ['users'],
    }

    for group_name, tables in groups.items():
        path = api_dir / f"{group_name}.py"
        lines = [
            "from fastapi import APIRouter, Depends",
            "from sqlalchemy.orm import Session",
            "from app.database import get_db",
        ]

        imported_models = []
        for tbl in tables:
            if tbl in table_info:
                cls_name = ''.join(w.capitalize() for w in tbl.split('_'))
                lines.append(f"from app.models import {cls_name}")
                imported_models.append((tbl, cls_name))

        lines.extend([
            "",
            "router = APIRouter()",
            "",
            "",
            f"@router.get('/{{}}'",
            f"def list_{group_name}(db: Session = Depends(get_db)):",
            f"    results = db.query({imported_models[0][1]}).all() if {imported_models} else []",
            f"    return [",
        ])

        if imported_models:
            tbl, cls = imported_models[0]
            cols = table_info[tbl]['columns']
            lines.append(f"        {{")
            for col in cols:
                key = col['name']
                val = f"str(p.{key})" if col['type'] == 'uuid' else f"p.{key}"
                lines.append(f"            '{key}': {val},")
            lines.append(f"        }}")
            lines.append(f"        for p in results")
            lines.append(f"    ]")

        path.write_text('\n'.join(lines))
        print(f"  ✓ {path}")


def generate_frontend(output_dir):
    """Generate React frontend scaffold."""
    src = output_dir / "frontend" / "src"
    src.mkdir(parents=True, exist_ok=True)

    # main.jsx
    (src / "main.jsx").write_text('''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
''')

    # App.jsx
    (src / "App.jsx").write_text('''import { useState, useEffect } from 'react'

const API = '/api'

export default function App() {
  const [data, setData] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([
      fetch(`${API}/products/`).then(r => r.json()),
      fetch(`${API}/categories`).then(r => r.json()),
      fetch(`${API}/sellers`).then(r => r.json()),
      fetch(`${API}/orders/`).then(r => r.json()),
      fetch(`${API}/users/`).then(r => r.json()),
    ])
      .then(([products, categories, sellers, orders, users]) => {
        setData({ products, categories, sellers, orders, users })
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  if (loading) return <div className="app"><div className="loading">Loading...</div></div>
  if (error) return <div className="app"><div className="error">Error: {error}</div></div>

  return (
    <div className="app">
      <header>
        <div className="app" style={{padding:'0'}}>
          <h1>🛒 Marketplace Dashboard</h1>
          <span style={{opacity:0.8}}>Data from PostgreSQL bigdata</span>
        </div>
      </header>

      <div className="stats">
        <div className="stat-card">
          <h3>Products</h3>
          <div className="value">{data.products?.length || 0}</div>
        </div>
        <div className="stat-card">
          <h3>Categories</h3>
          <div className="value">{data.categories?.length || 0}</div>
        </div>
        <div className="stat-card">
          <h3>Sellers</h3>
          <div className="value">{data.sellers?.length || 0}</div>
        </div>
        <div className="stat-card">
          <h3>Orders</h3>
          <div className="value">{data.orders?.length || 0}</div>
        </div>
        <div className="stat-card">
          <h3>Users</h3>
          <div className="value">{data.users?.length || 0}</div>
        </div>
      </div>

      {Object.entries(data).map(([key, items]) => (
        items && items.length > 0 && (
          <div className="table-section" key={key}>
            <h2>{key.charAt(0).toUpperCase() + key.slice(1)}</h2>
            <table>
              <thead>
                <tr>
                  {Object.keys(items[0]).map(k => (
                    <th key={k}>{k}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {items.slice(0, 20).map((item, i) => (
                  <tr key={i}>
                    {Object.values(item).map((v, j) => (
                      <td key={j} style={{fontFamily: j === 0 ? 'monospace' : 'inherit', fontSize: j === 0 ? 12 : 14}}>
                        {typeof v === 'string' && v.length > 12 ? v.slice(0, 8) + '...' : v}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      ))}
    </div>
  )
}
''')

    # index.html
    (output_dir / "frontend" / "index.html").write_text('''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Marketplace Dashboard</title>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #f5f5f5; color: #333; }
      .app { max-width: 1200px; margin: 0 auto; padding: 20px; }
      header { background: #1a73e8; color: white; padding: 20px 0; margin-bottom: 24px; }
      .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }
      .stat-card { background: white; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
      .stat-card h3 { font-size: 14px; color: #666; margin-bottom: 8px; }
      .stat-card .value { font-size: 32px; font-weight: bold; color: #1a73e8; }
      .table-section { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
      .table-section h2 { margin-bottom: 16px; font-size: 18px; }
      table { width: 100%; border-collapse: collapse; }
      th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid #eee; font-size: 14px; }
      th { background: #f8f9fa; font-weight: 600; color: #555; }
      .loading, .error { text-align: center; padding: 40px; }
      .error { color: #d32f2f; }
    </style>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
''')

    # vite.config.js
    (output_dir / "frontend" / "vite.config.js").write_text('''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
''')

    # package.json
    (output_dir / "frontend" / "package.json").write_text('''{
  "name": "marketplace-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "vite": "^6.0.0"
  }
}
''')

    print(f"  ✓ frontend/ (App.jsx, index.html, vite.config.js, package.json)")


def generate_docker(output_dir):
    """Generate docker-compose and Dockerfiles."""
    (output_dir / "docker-compose.yml").write_text('''version: "3.9"

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
    volumes:
      - ./backend:/app

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
''')

    (output_dir / "Dockerfile.backend").write_text('''FROM python:3.12-slim
WORKDIR /app
COPY backend/pyproject.toml .
RUN pip install --no-cache-dir .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
''')

    (output_dir / "Dockerfile.frontend").write_text('''FROM node:20-alpine
WORKDIR /app
COPY frontend/package.json ./
RUN npm ci
COPY frontend .
RUN npm run build

FROM nginx:alpine
COPY --from=frontend /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
''')

    (output_dir / "nginx.conf").write_text('''server {
    listen 80;
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
}
''')

    print(f"  ✓ docker-compose.yml, Dockerfile.backend, Dockerfile.frontend, nginx.conf")


def generate_readme(output_dir):
    """Generate README."""
    (output_dir / "README.md").write_text('''# Marketplace Dashboard

FastAPI + React web interface for PostgreSQL marketplace database.

## Quick Start

```bash
# Backend
cd backend
pip install -e .
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/products/` | List products |
| GET | `/api/orders/` | List recent orders |
| GET | `/api/users/` | List users |

## Structure

```
├── backend/app/     # FastAPI (models, schemas, routes)
├── frontend/src/    # React dashboard
├── docker-compose.yml
└── README.md
```
''')

    print(f"  ✓ README.md")


def main():
    parser = argparse.ArgumentParser(description="Scaffold FastAPI+React from PostgreSQL")
    parser.add_argument("--host", default="host.docker.internal", help="DB host")
    parser.add_argument("--port", type=int, default=6432, help="DB port")
    parser.add_argument("--dbname", default="bigdata", help="Database name")
    parser.add_argument("--user", default="postgres", help="DB user")
    parser.add_argument("--output", default=".", help="Output directory")
    args = parser.parse_args()

    print(f"Inspecting database at {args.host}:{args.port}/{argsdbname}...")
    table_info = inspect_tables(args.host, args.port, args.dbname, args.user)
    print(f"Found {len(table_info)} tables: {', '.join(sorted(table_info.keys()))}")

    output_dir = Path(args.output)
    print("\nGenerating project files:")
    generate_models(table_info, output_dir)
    generate_schemas(table_info, output_dir)
    generate_api_routes(table_info, output_dir)
    generate_frontend(output_dir)
    generate_docker(output_dir)
    generate_readme(output_dir)

    print(f"\nDone! Project scaffolded at {output_dir}")
    print(f"\nNext steps:")
    print(f"  1. cd {output_dir}/backend && DATABASE_URL=... uvicorn app.main:app --reload")
    print(f"  2. cd {output_dir}/frontend && npm install && npm run dev")
    print(f"  3. git init && git add -A && git commit -m 'feat: scaffold' && git push origin dev")


if __name__ == "__main__":
    main()
