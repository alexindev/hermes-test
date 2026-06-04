# Constrained VM Deployment — Session Detail

## Session: 2026-06-03 — Marketplace Backend on Yandex Cloud VM (Remote)

### Environment
- **VM**: `hermes@158.160.4.7` (Debian 11, Python 3.9)
- **Agent**: Inside Docker container (no root, no apt-get, no sudo)
- **Connection**: SSH with generated ed25519 key

### Steps Taken

1. **SSH key generation** — created `~/.ssh/id_ed25519` and shared public key with user
2. **Remote connection** — `ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_ed25519 hermes@158.160.4.7`
3. **Bootstrap pip on remote** — used `get-pip.py` for Python 3.9 (minimum supported)
4. **Install dependencies remotely** — `python3 -m pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings asyncpg psycopg2-binary alembic`
5. **Fix config.py** — added `debug`/`log_level` fields to Settings class
6. **Fix database.py** — added SQLite `check_same_thread=False` connect_args
7. **Fix models.py** — converted UUID PostgreSQL types → String(36), removed `uuid_generate_v4()` defaults
8. **Fix main.py** — changed from `api.products` to explicit `from app.api import products`
9. **Install nginx** — `sudo apt-get install -y nginx`
10. **Configure nginx reverse proxy** — `/etc/nginx/sites-available/marketplace` → proxy to `127.0.0.1:8000`
11. **Enable site** — symlink + remove default, `nginx -t`, `nginx -s reload`
12. **Start uvicorn** — `/home/hermes/.local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000`
13. **Verify** — `curl http://158.160.4.7/api/health` → `{"status":"ok"}`

### Key Patterns

#### Heredoc-free file writes over SSH
```bash
# BAD: complex Python with quotes in heredoc fails
ssh user@host "cat > file.py << 'EOF' ... EOF"

# GOOD: use python3 -c with pathlib
ssh user@host "python3 -c \"import pathlib; pathlib.Path('f.py').write_text('''code''')\""

# GOOD: use sudo tee for shell configs
ssh user@host 'sudo tee /path/to/file > /dev/null << '\''EOF'\''
content
EOF'
```

#### Nginx troubleshooting
- `sudo nginx -t` validates config before reload
- Symlink must exist: `ls -la /etc/nginx/sites-enabled/`
- If port 80 already bound: nginx is running, use `sudo nginx -s reload` not `sudo systemctl start`
- Empty sites-enabled directory = nginx uses default config (may not include your site)

### Files Modified (on VM)
- `~/hermes-test/backend/.env` — DATABASE_URL=sqlite:///./marketplace.db
- `~/hermes-test/backend/app/config.py` — added debug/log_level fields
- `~/hermes-test/backend/app/database.py` — SQLite connect_args
- `~/hermes-test/backend/app/models.py` — UUID→String conversion
- `~/hermes-test/backend/app/main.py` — explicit imports
- `/etc/nginx/sites-available/marketplace` — new nginx config
- `/etc/nginx/sites-enabled/marketplace` — symlink

### Notes
- Python 3.9 on Debian 11 requires `https://bootstrap.pypa.io/pip/3.9/get-pip.py` (not latest)
- pip installs to `~/.local/bin/` — full path needed or add to PATH
- Background processes via SSH need care — they run in the SSH session
- SQLite works for testing but loses data on restart (no persistence setup)