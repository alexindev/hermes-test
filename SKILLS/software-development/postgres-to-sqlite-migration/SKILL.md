---
name: postgres-to-sqlite-migration
description: Convert PostgreSQL-specific SQLAlchemy/FastAPI projects to SQLite for local dev or environments without Postgres — UUID types, defaults, engine config.
tags: [migration, sqlite, sqlalchemy, fastapi]
---

# PostgreSQL → SQLite Migration for SQLAlchemy Projects

Convert a PostgreSQL-backed SQLAlchemy project to SQLite when Postgres is unavailable or unnecessary (local dev, constrained VMs).

## When to Use

- PostgreSQL connection unavailable (network, permissions, missing container)
- Need quick local development setup
- Deploying on a restricted VM without system packages
- Prototyping before committing to Postgres

## Migration Checklist

### 1. Update DATABASE_URL

```python
# Before (PostgreSQL)
DATABASE_URL=postgresql+psycopg2://user:pass@host:port/dbname

# After (SQLite)
DATABASE_URL=sqlite:///./marketplace.db
```

### 2. Fix `database.py` — SQLite connect args

```python
from sqlalchemy import create_engine
from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)
```

Without `check_same_thread=False`, SQLite raises `InterfaceError: Error binding parameter`.

### 3. Replace UUID column types

SQLAlchemy's `UUID(as_uuid=True)` and `server_default=text("uuid_generate_v4()")` don't work with SQLite.

**Before (PostgreSQL):**
```python
from sqlalchemy.dialects.postgresql import UUID

class User(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
```

**After (SQLite):**
```python
import uuid

def _uuid_default():
    return str(uuid.uuid4())

class User(Base):
    id = Column(String(36), primary_key=True, default=_uuid_default)
```

### 4. Replace PostgreSQL-specific defaults

| PostgreSQL | SQLite replacement |
|-----------|-------------------|
| `text("uuid_generate_v4()")` | `default=_uuid_default` |
| `text("now()")` | `default=lambda: datetime.now()` or `server_default=text("datetime('now')")` |
| `text("'created'::order_status")` | `text("'created'")` |
| `Numeric(10, 2)` | Keep as-is (works in both) |
| `ForeignKey("table.col")` | Keep as-is (SQLite supports FKs, just doesn't enforce by default) |

### 5. Handle JSON/TEXT differences

SQLite has no native JSON or enum types. Use:
- `String` for text data
- `Text` for large text
- `JSON` type works in both (stored as text in SQLite)

### 6. Alembic migration notes

If using Alembic:
```bash
# Generate migration after model changes
alembic revision --autogenerate -m "migrate to sqlite"
alembic upgrade head
```

SQLite has limited ALTER TABLE support. For complex schema changes, consider:
- Dropping and recreating tables
- Using `alembic` with `--sql` flag for offline mode

### 7. Query compatibility issues

Some PostgreSQL queries don't work in SQLite:
- `ILIKE` → use `LIKE` (case-sensitive) or `.lower()` in Python
- `NOW()` → `datetime('now')`
- `GENERATE_SERIES()` → Python `range()`
- Window functions may have limited support

## Reference Files

- See `references/postgres-sqlite-migration.md` for session-specific examples.