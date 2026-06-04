---
name: local-to-vm-deploy
description: "Standard workflow: make changes locally → commit to GitHub → create PR → user approves → deploy on remote VM via SSH."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [GitHub, Deployment, Docker, SSH, Workflow]
    related_skills: [github-pr-workflow, docker-browserless-setup]
---

# Local Development → GitHub → Remote Deploy Workflow

Standard workflow for making code changes, reviewing via PR, and deploying to a remote VM.

## Core Principle

**Always work locally first.** Never modify files directly on the remote VM.

```
Local (code + git + gh) → GitHub PR → User approves → VM (pull + deploy)
```

## Steps

### 1. Make Changes Locally

Work in the project directory (e.g., `/opt/data/hermes-test`). Use file tools to edit code.

```bash
cd /opt/data/hermes-test
git checkout main && git pull origin main
git checkout -b feat/description
# ... make changes with file tools ...
```

### 2. Commit and Push

```bash
git add -A
git commit -m "feat: description of changes"
git push -u origin HEAD
```

### 3. Create PR

Use `gh` CLI locally (it's authenticated). The VM typically has NO GitHub access.

```bash
~/bin/gh pr create \
  --base main \
  --head feat/description \
  --title "feat: title" \
  --body "description"
```

### 4. Wait for User Approval

Do NOT proceed until the user merges the PR. Ask the user to review and approve.

### 5. Deploy on VM (after merge)

Only after the user confirms the PR is merged:

```bash
# SSH to VM
ssh user@vm-host "cd ~/project && git checkout main && git pull origin main"

# Deploy (example: docker-compose)
ssh user@vm-host "cd ~/project && sudo docker compose up -d --build"
```

## ⚠️ Pitfalls

### VM has no GitHub access
The remote VM usually lacks:
- SSH keys for GitHub
- `gh` CLI authentication
- PAT tokens

**Solution**: do all git/PR work locally. Only SSH to VM for deployment commands.

### Never commit secrets
`.env` files with database passwords, API keys, etc. must NOT be committed.

**Pattern**:
- Create `.env.example` (or `.env.template`) with placeholder values
- Add `.env` to `.gitignore`
- Document connection strings in the example file

```bash
# Wrong: committing .env
git add backend/.env

# Right: commit template, ignore real .env
git add backend/.env.example
# .env is already in .gitignore
```

### VM only works with `main` branch
After merge, pull `main` on the VM. Never deploy from feature branches.

### Docker Compose service names matter
Inside docker-compose network, services reach each other by **service name**, not `localhost` or IP.

```yaml
# In docker-compose.yml
services:
  postgres:        # ← this name is the hostname inside the network
    image: postgres:18-alpine
  backend:
    depends_on:
      postgres:
        condition: service_healthy
    env_file:
      - .env       # DATABASE_URL=postgresql://user:pass@postgres:5432/db

# In .env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@postgres:5432/bigdata
#                                          ↑ service name, NOT localhost
```

### Multi-stage frontend builds
### Multi-stage frontend builds
React/Vue frontend needs build step before serving. Use multi-stage Dockerfile:
```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build          # produces dist/

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html   # serve built files
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Docker Compose may not be installed on VM
Some VMs have Docker CLI but no compose plugin. If `docker compose` fails with "is not a docker command":

```bash
# Install compose plugin to user directory (no root needed)
mkdir -p ~/.docker/cli-plugins
curl -SL https://github.com/docker/compose/releases/download/v2.32.4/docker-compose-linux-x86_64 \
  -o ~/.docker/cli-plugins/docker-compose
chmod +x ~/.docker/cli-plugins/docker-compose
docker compose version  # verify
```

### IPv6 connectivity breaks Docker Hub pulls on VM
VMs without IPv6 get TLS cert verification failures when Docker resolves registry-1.docker.io to IPv6-first. Symptoms: `tls: failed to verify certificate: x509: certificate signed by unknown authority`.

**Fix**: ensure Docker uses IPv4 only. Either:
- Set `/etc/docker/daemon.json` with `"preferences": {"network": {"ipv4": true}}` (needs root)
- Or use `--network` flag in compose if services can work over IPv4
- Or fix DNS/networking to prefer A records over AAAA

### Python slim images have outdated setuptools
`python:*-slim` images ship old setuptools that can't parse modern `pyproject.toml` build backends. When `pip install .` fails with `setuptools.backends._legacy:_Backend`:

```dockerfile
# Before pip install, upgrade build tools
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir .
```

This applies to both backend and any other Python service using pyproject.toml with setuptools build backend.

## Common Service Chain

```
frontend (nginx:80) → backend (fastapi:8000) → postgres (5432)
```

Docker Compose ordering:
1. `postgres` starts first (no dependencies)
2. `backend` waits for `postgres` healthy
3. `frontend` waits for `backend` healthy
