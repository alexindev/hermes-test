---
name: container-deployment
description: Deploying services in Docker containers — compose files, networking gotchas, datasource binding, and monitoring stacks (Prometheus/Grafana/Node Exporter).
---

# Container Deployment & Monitoring

## Docker Environment Rules

### Problem
Hermes Agent runs inside Docker. `/opt/hermes/` is root-owned (mounted volume). Container user is UID 1000. System Python is externally managed (PEP 668).

### Rule: NEVER install packages into these locations
- `/opt/hermes/` — root-owned, permission denied
- System Python — externally managed
- Any `.venv` found by `uv` in parent directories

### Correct approach: use /opt/data/hermes-tools/.venv

```bash
# Install into correct venv
/opt/data/hermes-tools/.venv/bin/pip install <package>

# Or with uv (explicit python)
uv pip install --python /opt/data/hermes-tools/.venv/bin/python <package>

# Run scripts with the tools venv
/opt/data/hermes-tools/.venv/bin/python script.py
```

### Helper script
`/opt/data/bin/hermes-tools` — wrapper for running Python commands in the tools venv.

### When creating new venvs
Always use `/opt/data/` as the base directory. Never use `/opt/hermes/`.

### Verification
After installing, always verify:
```bash
/opt/data/hermes-tools/.venv/bin/python -c "import <package>; print('OK')"
```

## Docker Networking Gotcha: host.docker.internal

`host.docker.internal` works on macOS/Windows Docker Desktop but **does NOT work on Linux**.

When a container needs to reach a service on the host (e.g., Node Exporter on port 9100):

```bash
# WRONG — doesn't work on Linux
targets: ["localhost:9100"]
targets: ["host.docker.internal:9100"]

# CORRECT — use Docker gateway IP
# Find it with: docker network inspect <network> | grep Gateway
targets: ["172.18.0.1:9100"]
```

**Debug pattern:**
1. Check if service is reachable from container: `docker exec <container> wget -qO- http://<host-ip>:<port>`
2. Get Docker gateway: `docker network inspect <network> --format '{{(index .IPAM.Config 0).Gateway}}'`
3. Use that IP in Prometheus scrape configs

## Grafana Datasource Binding

When creating dashboards via API, panels default to `datasource: NONE`. Must explicitly bind them.

```python
prom_ds_uid = "afo1076a7n3eoa"  # get from /api/datasources

for panel in dashboard["panels"]:
    panel["datasource"] = {"uid": prom_ds_uid, "type": "prometheus"}
    for target in panel.get("targets", []):
        target["datasource"] = {"uid": prom_ds_uid, "type": "prometheus"}
```

**To find datasource UIDs:**
```bash
curl -u admin:password http://grafana:3000/api/datasources
# Look for "uid" field in response
```

## Prometheus Reload

After changing config, reload without restart:
```bash
curl -X POST http://localhost:9090/-/reload
```

Requires `--web.enable-lifecycle` flag in prometheus command.

## Reference Files
- `references/prometheus-setup.md` — full Prometheus + Node Exporter + Grafana stack setup
- `templates/docker-compose-monitoring.yml` — ready-to-use compose file
