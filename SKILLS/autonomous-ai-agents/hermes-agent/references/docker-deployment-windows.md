# Docker Desktop on Windows — Socket Access

When running Hermes Agent inside a container on **Windows Docker Desktop**, the Docker socket (`/var/run/docker.sock`) is **not natively available** as a Unix socket — Docker Desktop uses a named pipe (`//./pipe/docker_engine`).

## Two working approaches

### Option A — Group-add technique (preferred)

On Windows Docker Desktop, the socket IS available inside Linux containers but belongs to `root:root`. Give the `hermes` user group access:

```powershell
docker run -d `
  -v hermes-data:/opt/data `
  -v /var/run/docker.sock:/var/run/docker.sock `
  --group-add 0 `
  -e HERMES_UID=1000 `
  --name hermes `
  hermes-agent `
  hermes gateway run
```

`--group-add 0` adds the `root` group (GID 0) to the `hermes` user's supplementary groups — enough for socket access without running as root.

### Option B — TCP mode

Enable **"Expose daemon on tcp://localhost:2375 without TLS"** in Docker Desktop → Settings → General, then:

```powershell
docker run -d `
  -v hermes-data:/opt/data `
  -p 2375:2375 `
  -e DOCKER_HOST=tcp://host.docker.internal:2375 `
  --add-host host.docker.internal:host-gateway `
  --group-add 0 `
  -e HERMES_UID=1000 `
  --name hermes `
  hermes-agent `
  hermes gateway run
```

### Option C — Named pipe (WSL2 backend only)

```powershell
docker run -d `
  -v hermes-data:/opt/data `
  -v //./pipe/docker_engine://./pipe/docker_engine `
  --group-add 0 `
  -e HERMES_UID=1000 `
  --name hermes `
  hermes-agent `
  hermes gateway run
```

The named pipe approach only works when Docker Desktop runs in **WSL2 mode** (the default).

## Startup delay with Docker socket

When the Docker socket is available, Hermes may attempt to check/pull the `terminal.docker_image` (e.g. `nikolaika/python-nodejs:python3.11-nodejs20`). If the image is not cached locally or the network is slow, this can cause a **~5-minute timeout** at startup. Mitigations:

- Set `terminal.docker_image: ""` in config.yaml to disable Docker-backed terminal execution
- Pre-pull the image: `docker pull nikolaika/python-nodejs:python3.11-nodejs20`
- Use `terminal.backend: local` explicitly to force local terminal