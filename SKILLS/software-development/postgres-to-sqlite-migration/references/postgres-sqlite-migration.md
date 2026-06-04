# PostgreSQL → SQLite Migration — Session Detail

## Session: 2026-06-03 — Marketplace Backend (hermes-test)

### Context
Project deployed on Yandex Cloud VM. Original DB was PostgreSQL on Docker Desktop host (`host.docker.internal:6432/bigdata`). `host.docker.internal` doesn't resolve from cloud VMs — network isolation. Chose SQLite for quick deployment.

### Changes Made

#### models.py — Full rewrite of column definitions

**UUID columns:**
```python
# Before (PostgreSQL)
id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))

# After (SQLite)
def _uuid_default():
    return str(uuid.uuid4())

id = Column(String(36), primary_key=True, default=_uuid_default)
```

**Timestamp columns:**
```python
# Before
created_at = Column(Timestamp, server_default=text("now()"))

# After  
def _now_default():
    return text("datetime('now')")

created_at = Column(DateTime, server_default=_now_default())
```

**Boolean/default columns:**
```python
# Before
status = Column(String(50), nullable=False, server_default=text("'created'::order_status"))
stock = Column(Integer, server_default=text("0"))

# After
status = Column(String(50), nullable=False, server_default=text("'created'"))
stock = Column(Integer, server_default=text("0"))  # unchanged — works in both
```

**Removed import:**
```python
# Removed
from sqlalchemy.dialects.postgresql import UUID
```

#### database.py — Added SQLite connect args

```python
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)
```

#### config.py — Added missing fields

```python
class Settings(BaseSettings):
    database_url: str
    debug: bool = False
    log_level: str = "info"
```

#### main.py — Fixed import pattern

```python
# Before (broken — api/__init__.py was empty)
from app import api
app.include_router(api.products, ...)

# After
from app.api import products, users, orders
app.include_router(products.router, ...)
```

#### .env — Changed database URL

```
DATABASE_URL=sqlite:///./marketplace.db
```

### Verification

```bash
curl http://localhost:8000/api/health   # {"status":"ok"}
curl http://localhost:8000/api/products/ # []
curl http://localhost:8000/api/users/    # []
```

Database created at: `/opt/data/hermes-test/backend/marketplace.db`

### Important Notes

- The project uses SQLAlchemy 2.0 style declarative models — compatible with SQLite
- Foreign keys are defined but not enforced by SQLite by default (`PRAGMA foreign_keys = ON` to enable)
- No data migration needed — fresh tables created on startup via `Base.metadata.create_all()`