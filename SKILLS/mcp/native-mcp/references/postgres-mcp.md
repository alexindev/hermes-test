# Postgres MCP Pro (crystaldba/postgres-mcp)

## Package info
- PyPI: `postgres-mcp`
- Docker: `crystaldba/postgres-mcp`
- GitHub: https://github.com/crystaldba/postgres-mcp

## Hermes Agent config (uvx transport)

```yaml
mcp_servers:
  postgres:
    command: "uvx"
    args: ["postgres-mcp", "--access-mode=unrestricted"]
    env:
      DATABASE_URI: "postgresql://user:pass@host:port/dbname"
```

## Hermes Agent config (Docker transport)

```yaml
mcp_servers:
  postgres:
    command: "docker"
    args: ["run", "-i", "--rm", "-e", "DATABASE_URI", "crystaldba/postgres-mcp", "--access-mode=unrestricted"]
    env:
      DATABASE_URI: "postgresql://user:pass@host.docker.internal:port/dbname"
```

## SSE transport (containerized MCP server)

Start server:
```bash
docker run -i --rm \
  -e DATABASE_URI="postgresql://user:pass@host:port/dbname" \
  crystaldba/postgres-mcp --transport=sse
```

Client config:
```yaml
mcp_servers:
  postgres:
    url: "http://host.docker.internal:8000/sse"
    transport: sse   # REQUIRED — without this Hermes sends POST and gets 405
```

## Key tools exposed
- Health checks, index tuning, EXPLAIN plans, schema introspection, safe SQL execution
- Requires `pg_stat_statements` and `hypopg` extensions for full feature set

## Pitfalls
- `host.docker.internal` only works when Hermes runs inside a Docker container. If Hermes is on the host directly, use the actual Docker bridge IP (e.g. `172.17.0.1`) or the database host.
- `--access-mode=unrestricted` allows write queries. Use read-only mode for safety in production.
- The `DATABASE_URI` must use `postgresql://` scheme (not `postgres://`).
- **Silent failure pattern:** postgres-mcp does NOT crash when the DB is unreachable — it logs WARNING-level messages and keeps the server running. The agent sees "no tools available" or generic errors. Always verify connectivity by checking the MCP server process output for connection errors before assuming the MCP layer is broken.
- **Non-standard ports are common.** PostgreSQL may run on any port (e.g. 6432 instead of 5432). Check the DATABASE_URI in config.yaml carefully — the port may differ from the default.
- **Hermes credential pool masks passwords** as `***` in config.yaml. You cannot read the real password from the config file. Verify connectivity by inspecting the MCP server process logs or testing with a separate connection attempt.
- **`transport: sse` vs `type: sse`** — Hermes checks `config.get("transport") == "sse"` (in mcp_tool.py:1313). Config key `type: sse` is silently ignored, causing Hermes to fall back to StreamableHTTP (POST) and get 405 Method Not Allowed. Always use `transport: sse`, never `type: sse`.
- **Multiple MCP sections in config.yaml** — the gateway reads `mcp_servers` (one word, nested under `mcp_servers` key). Some configs also contain `mcp.server.postgres` (Seamless MCP format) — that section is NOT read by Hermes's native MCP client and can create confusion. Only `mcp_servers` is active.
