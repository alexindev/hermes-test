# Crystaldba postgres-mcp: Deployment & Network Troubleshooting

Source: session 2026-06-01. User runs Hermes in a Docker container on Windows Docker Desktop. MCP server deployed as a separate container on the same host.

## Deployment (Docker)

```bash
docker run -d --name postgres-mcp \
  -p 5430:8000 \
  -e DATABASE_URI="postgresql://postgres:password@host.docker.internal:6432/bigdata" \
  crystaldba/postgres-mcp \
  --access-mode=restricted
```

- Internal port: **8000** (inside container)
- Host port: **5430** (mapped via `-p 5430:8000`)
- Image: `crystaldba/postgres-mcp`
- The `--access-mode=restricted` flag enforces read-only mode in the MCP tools

## Endpoint Architecture

| Mode | Internal Port | External Port | How to call |
|------|---------------|---------------|-------------|
| HTTP (default) | 8000 | 5430 | `POST /rpc` with JSON-RPC payload |
| SSE (`--transport=sse`) | 8000 | 5430 | `GET /sse` → subscribe → obtain session URL → POST messages |

**Default transport is NOT SSE** — it uses plain HTTP JSON-RPC at `/rpc`.

### Testing

```bash
# Check if port is reachable at all
curl -s --connect-timeout 3 http://host.docker.internal:5430/rpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

Expected successful response includes JSON with `"jsonrpc":"2.0"` and a `result` field.

### Paths that DO NOT work (return empty reply)

- `GET /` — empty reply
- `GET /health` — empty reply  
- `POST /mcp/v1` — empty reply
- `GET /sse` — empty reply (unless SSE transport enabled)
- `POST /tools` — empty reply

## Docker Desktop IPv6 Problem

`host.docker.internal` on Docker Desktop resolves to BOTH IPv4 and IPv6:
- IPv4: `192.168.65.254`
- IPv6: `fdc4:f303:9324::254`

DNS resolution order favours IPv6. When the IPv6 route doesn't exist (common in WSL2-based Docker Desktop), all connections to the IPv6 address fail silently.

### Symptoms
- TCP handshake succeeds but HTTP returns **empty reply** (`curl: (52) Empty reply from server`)
- All endpoints return nothing
- `curl --ipv4` works, default curl doesn't
- Python `urllib.request` gets `RemoteDisconnected: Remote end closed connection without response`
- Browser can't load the page

### Resolution
1. **Force IPv4**:
   ```bash
   curl --ipv4 http://host.docker.internal:5430/rpc ...
   ```
2. **Use `gateway.docker.internal`** (resolves to `192.168.65.1`, different subnet — may or may not work depending on port mapping)
3. **Add IPv4 to `/etc/hosts`**:
   ```bash
   echo "192.168.65.254 host.docker.internal" >> /etc/hosts
   ```
4. **Python code**:
   ```python
   import socket
   import urllib.request
   
   # Force IPv4 resolution
   ip = socket.getaddrinfo("host.docker.internal", 5430, socket.AF_INET)[0][4][0]
   url = f"http://{ip}:5430/rpc"
   ```

## Container Network Isolation

If Hermes and postgres-mcp are in DIFFERENT Docker networks, the agent cannot reach the MCP server even though the port is published on the host.

**Fix**: Join both containers to the same Docker network:
```bash
docker network create hermes-net
docker network connect hermes-net postgres-mcp
docker network connect hermes-net hermes
```

Then use `http://postgres-mcp:8000/rpc` instead of `http://host.docker.internal:5430/rpc`.