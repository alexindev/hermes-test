# Deployment Troubleshooting Patterns

## PostgreSQL Password Hidden in Docker

When `docker inspect` shows `***` for passwords:

```bash
# Wrong - reveals masked value
docker inspect <container> --format '{{.Config.Env}}'

# Right - read from container environment at runtime
docker exec <container> env | grep PASSWORD
```

## Non-Docker Deployment (Fallback)

When Docker is unavailable on target host:

1. **Install Python deps**: `curl https://bootstrap.pypa.io/get-pip.py | python3` then `pip install fastapi uvicorn sqlalchemy pydantic`
2. **Install Node.js** (for frontend): `curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash - && sudo apt-get install -y nodejs`
3. **Build frontend**: `npm install && npm run build`
4. **Run backend**: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
5. **Nginx config**: proxy_pass to `http://127.0.0.1:8000` (not `backend:8000`)

## SQLite vs PostgreSQL Model Differences

SQLite doesn't support UUID server_default or `datetime('now')` as server_default. Workarounds:

- Use `String(36)` with `default=_uuid_func()` instead of `UUID` type
- Remove `server_default=text('now()')` — set timestamps in application code
- Remove `server_default=text("0")` — use `default=0`

## SSH Access to VM Without Keys

1. Generate key: `ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""`
2. Share public key with user
3. User adds to `~/.ssh/authorized_keys` on target
4. Connect: `ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_ed25519 user@host`
