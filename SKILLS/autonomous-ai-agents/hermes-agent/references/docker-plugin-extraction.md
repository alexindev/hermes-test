# Extracting Plugins from Running Hermes Docker Container

When Hermes runs inside Docker with source mounted (editable install), plugins live inside the container at `/opt/hermes/plugins/`. To extract them for version control or backup:

## Step 1: Find the container

```bash
docker ps --format '{{.ID}} {{.Names}}' | grep hermes
# Example: 385bb8bc159b hermes
```

## Step 2: Locate the plugin

```bash
# Search by name pattern
docker exec <container_id> find /opt/hermes/plugins -name "*vk*" -type f 2>/dev/null

# Or search for any custom platform plugin
docker exec <container_id> find /opt/hermes/plugins/platforms -type f 2>/dev/null
```

## Step 3: Read and copy files

```bash
# Read the full file
docker exec <container_id> cat /opt/hermes/plugins/platforms/<name>/adapter.py

# Or copy entire directory to host
docker cp <container_id>:/opt/hermes/plugins/platforms/<name> /host/path/
```

## Key paths

| Location | Purpose |
|----------|---------|
| `/opt/hermes/plugins/` | In-code plugins (shipped with Hermes) |
| `/opt/data/plugins/` | User-installed plugins (host-mounted) |
| `$HERMES_HOME/plugins/` | Alternative user plugin path |

## Pitfalls

- **Editable install**: The container maps `/opt/hermes` as an editable install. Changes on the host at `/opt/data/plugins/` appear in-container automatically — no rebuild needed.
- **`__pycache__`**: Skip `.pyc` files; only version the `.py` sources and `plugin.yaml`.
- **Plugin manifest**: Always check `plugin.yaml` for required env vars before extracting. It documents what the adapter needs.
