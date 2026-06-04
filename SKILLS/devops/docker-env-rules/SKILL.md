---
name: docker-env-rules
description: Rules for managing Python packages and Docker deployments inside/outside Docker containers — never install into /opt/hermes/ (root-owned) or system Python. Use /opt/data/hermes-tools/.venv for local tools. Remote Docker deployment via SSH + docker-compose.
---

# Docker Environment Rules

## Problem
Hermes Agent runs inside Docker. `/opt/hermes/` is root-owned (mounted volume). Container user is UID 1000. System Python is externally managed (PEP 668).

## Rule: NEVER install packages into these locations
- `/opt/hermes/` — root-owned, permission denied
- System Python — externally managed
- Any `.venv` found by `uv` in parent directories

## Correct approach: use /opt/data/hermes-tools/.venv

```bash
# Install into correct venv
/opt/data/hermes-tools/.venv/bin/pip install <package>

# Or with uv (explicit python)
uv pip install --python /opt/data/hermes-tools/.venv/bin/python <package>

# Run scripts with the tools venv
/opt/data/hermes-tools/.venv/bin/python script.py
```

## Helper script
`/opt/data/bin/hermes-tools` — wrapper for running Python commands in the tools venv.

## When creating new venvs
Always use `/opt/data/` as the base directory. Never use `/opt/hermes/`.

## Verification
After installing, always verify:
```bash
/opt/data/hermes-tools/.venv/bin/python -c "import <package>; print('OK')"
```

---

# Remote Docker Deployment

## Pattern: deploy docker-compose stacks on remote servers via SSH

### Prerequisites
- SSH key configured for the target server
- Docker Engine installed on the server
- User added to `docker` group (or running as root)

### Steps

1. **Create files locally** — write docker-compose.yml, config files, scripts
2. **Transfer via SCP** — copy to remote server:
   ```bash
   scp -i <key> <files> hermes@<server_ip>:~/monitoring/
   ```
3. **SSH to run** — execute compose commands remotely:
   ```bash
   ssh -i <key> hermes@<server_ip> 'cd ~/monitoring && docker compose up -d'
   ```
4. **Verify** — check containers are running:
   ```bash
   ssh -i <key> hermes@<server_ip> 'docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
   ```

### Common pitfalls
- **Permission denied on SSH**: ensure private key exists and has correct permissions (600)
- **Docker permission denied**: add user to docker group: `sudo usermod -aG docker <user>`
- **Compose version warning**: remove `version: "3.8"` from compose files (obsolete, ignored)
- **Image pull timeout**: large images (grafana, prometheus) may take time — use background execution or wait patiently
- **Network mode host**: node_exporter needs `network_mode: host` and `pid: host` to read host metrics

### Reference files
- `references/grafana-dashboard-automation.md` — programmatic Grafana dashboard creation via API
- `references/remote-deploy-troubleshooting.md` — common issues and fixes for remote Docker deployments
- `references/ssh-connection-pattern.md` — SSH connection patterns for remote server management
