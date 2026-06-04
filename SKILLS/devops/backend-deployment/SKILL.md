---
name: backend-deployment
description: Deploy Python/FastAPI backends on restricted VMs (no apt-get, no root) — bootstrap pip, fix pydantic_settings, handle import issues, run uvicorn.
---

# Backend Deployment on Constrained Environments

Deploy Python/FastAPI backends on VMs where `apt-get`, `sudo`, or package managers are unavailable.

## When to Use

- Fresh VM (Debian/Ubuntu/CentOS) with no pip, no venv tools
- No root/sudo access
- Cannot install system packages
- Need to run a Python web service quickly

## Prerequisites Check

```bash
which python3 && python3 --version
```

If `pip` is missing but `python3` exists:

### Bootstrap pip

```bash
curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
python3 /tmp/get-pip.py
```

If `python3` itself is missing, you're stuck — need root or a different VM.

## Deployment Steps

### 1. Install dependencies

```bash
pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings
```

### 2. Fix pydantic_settings validation

If `.env` has keys not in your `Settings` class, you'll get:

```
Extra inputs are not permitted [type=extra_forbidden]
```

**Fix**: Add all `.env` keys to the `BaseSettings` class with defaults:

```python
class Settings(BaseSettings):
    database_url: str
    debug: bool = False          # ← must exist if .env has DEBUG
    log_level: str = "info"      # ← must exist if .env has LOG_LEVEL
    model_config = {"env_file": ".env"}
```

### 3. Fix empty `__init__.py` import issues

If code does `from app.api import products` but `api/__init__.py` is empty:

```
AttributeError: module 'app.api' has no attribute 'products'
```

**Fix**: Import submodules explicitly in `main.py`:

```python
from app.api import products, users, orders  # explicit imports
# NOT: from app import api; api.products.router
```

Or populate `api/__init__.py`:

```python
from . import products, users, orders
```

### 4. Run the server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 5. Verify

```bash
curl http://localhost:8000/api/health
```

## Remote VM Deployment via SSH

When the target VM is reachable via SSH (not localhost):

### 1. Generate SSH key if missing

```bash
mkdir -p ~/.ssh && ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N "" -q
cat ~/.ssh/id_ed25519.pub  # share public key with VM admin
```

### 2. Connect and diagnose

```bash
ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_ed25519 user@host "whoami; hostname; cat /etc/os-release | head -3"
```

### 3. Run commands remotely

Use `sudo` for system-level operations (apt-get, nginx):

```bash
ssh -i ~/.ssh/id_ed25519 user@host "sudo apt-get update && sudo apt-get install -y nginx"
```

### 4. Write files remotely (heredoc-safe)

Avoid bash heredocs with complex Python code (quoting nightmares). Use `python3 -c` with pathlib instead:

```bash
ssh -i ~/.ssh/id_ed25519 user@host "python3 -c \"
import pathlib
pathlib.Path('app/models.py').write_text('''
from sqlalchemy import Column, String
...
''')
print('done')
\""
```

Or use `tee` with sudo:

```bash
ssh -i ~/.ssh/id_ed25519 user@host 'sudo tee /etc/nginx/sites-available/marketplace > /dev/null << '\''EOF'\''
server { ... }
EOF'
```

### 5. Start services remotely

```bash
ssh -i ~/.ssh/id_ed25519 user@host "cd ~/project && uvicorn app.main:app --host 0.0.0.0 --port 8000"
```

## Nginx Reverse Proxy Setup

Install and configure nginx as a reverse proxy for FastAPI:

### 1. Install nginx

```bash
sudo apt-get update && sudo apt-get install -y nginx
```

### 2. Create site config

```nginx
server {
    listen 80;
    server_name _;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 5s;
        proxy_read_timeout 30s;
    }

    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
}
```

### 3. Enable and test

```bash
sudo ln -sf /etc/nginx/sites-available/marketplace /etc/nginx/sites-enabled/marketplace
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t          # verify config
sudo nginx -s reload   # or restart if not running
```

### 4. Verify through nginx

```bash
curl http://localhost/api/health
```

## Common Pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| `pip: command not found` | No pip installed | Bootstrap via get-pip.py |
| `ensurepip not available` | Python built without ensurepip | Use get-pip.py directly |
| `Extra inputs are not permitted` | pydantic_settings rejects unknown env vars | Add fields to Settings class |
| `module has no attribute` | Empty `__init__.py` + dotted import | Use explicit imports |
| Port already in use | Previous uvicorn still running | Kill process or use different port |
| `Permission denied` on /etc/nginx/* | Need sudo | Use `sudo tee` or run as root |
| nginx config test passes but 404 | Symlink broken or old config cached | Check `ls -la sites-enabled/`, run `sudo nginx -s reload` |
| `bind() to 0.0.0.0:80 failed (98)` | nginx already running | Don't start again; use `sudo nginx -s reload` |
| Heredoc fails with syntax error | Single quotes inside Python code | Use `python3 -c` with pathlib instead |

## References

- See `references/constrained-vm-deployment.md` for session-specific details and examples.
- See `templates/nginx-fastapi-proxy.conf` for a ready-to-use nginx reverse proxy config.
- See `scripts/write_remote.py` for a helper to write files remotely without heredoc quoting issues.