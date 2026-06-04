# Upgrading Hermes Agent in Docker / Permission-Restricted Environments

## Problem

Dashboard shows "X commits behind — run uv pip install --upgrade hermes-agent".
Common in Docker deployments where the container user (e.g. `hermes` UID 1000)
cannot write to host-owned files (e.g. `pyproject.toml` owned by UID 10000).

## Diagnosis

```bash
# Check installed version
grep "^version" /opt/hermes/pyproject.toml

# Check latest on PyPI
curl -s https://pypi.org/pypi/hermes-agent/json | python3 -c "import sys,json; print(json.load(sys.stdin)['info']['version'])"

# Check if pip exists in venv
ls /opt/hermes/.venv/bin/pip 2>/dev/null || echo "no pip in .venv"

# Check uid mismatch
ls -la /opt/hermes/pyproject.toml
id
```

## Fix Options

### Option A: `hermes update` (works if user has file access)
```bash
hermes update
```

### Option B: Manual upgrade with `uv` (when `uv` is available)
```bash
cd /opt/hermes
sed -i 's/version = "0.14.0"/version = "0.15.1"/' pyproject.toml
uv pip install -e .
```

### Option C: Manual upgrade with `pip` (when `pip` exists in .venv)
```bash
cd /opt/hermes
sed -i 's/version = "0.14.0"/version = "0.15.1"/' pyproject.toml
pip install -e .
```

### Option D: If neither `uv` nor `pip` in .venv
The Hermes-installed venv is stripped for install size. Install pip first:
```bash
python3 -m ensurepip --upgrade
# then use pip install -e .
```

## Pitfalls

- **Editable installs**: `pip install --upgrade hermes-agent` does NOT work when
  the package is installed as editable (`__editable__.xxx.pth`). You must update
  `pyproject.toml` version AND reinstall with `-e .`.
- **No pip in .venv**: Hermes ships a minimal venv. `ensurepip` or `get-pip.py`
  may be needed before `pip install`.
- **Permission denied**: Docker container user often has different UID than
  host file owner. Use `sudo` if available, or run the upgrade commands
  from outside the container.
- **No sudo**: Some containers don't have sudo. In that case, the user must
  fix permissions on the host side.
