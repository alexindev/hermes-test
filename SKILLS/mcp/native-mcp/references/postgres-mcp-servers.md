# Verified PostgreSQL MCP Servers

## crystaldba/postgres-mcp (Postgres MCP Pro)

**Repo:** https://github.com/crystaldba/postgres-mcp  
**PyPI:** https://pypi.org/project/postgres-mcp/  
**Docker:** `crystaldba/postgres-mcp`

### Key features
- Schema Intelligence — context-aware SQL generation from database schema understanding
- Safe SQL Execution — configurable access control, read-only mode, safe SQL parsing
- EXPLAIN Plans — validate and optimize performance by reviewing execution plans
- Index Tuning — explore thousands of possible indexes for best workload solution
- Database Health — analyze index health, connection utilization, buffer cache, vacuum health, replication lag
- Two transports: stdio (subprocess) and SSE (HTTP)

### Hermes integration (SSE transport)

```yaml
mcp_servers:
  postgres:
    url: "http://host.docker.internal:8000/sse"
    timeout: 180
```

### Docker run command

```bash
docker run -d --name postgres-mcp \
  -e DATABASE_URI="postgresql://user:pass@host:port/db" \
  -p 8000:8000 \
  crystaldba/postgres-mcp \
  --access-mode=unrestricted --transport=sse
```

For read-only mode, use appropriate access-mode flag.

### Hermes integration (stdio transport)

```yaml
mcp_servers:
  postgres:
    command: "docker"
    args: ["run", "-i", "--rm", "-e", "DATABASE_URI", "crystaldba/postgres-mcp", "--access-mode=unrestricted"]
    env:
      DATABASE_URI: "postgresql://user:pass@host:port/db"
```

### Architecture pattern (validated in session)

When building an NL-to-SQL assistant:
- **Skill** = business logic / semantics (what "best" means, terminology mapping)
- **MCP server** = SQL execution engine (runs the queries, provides schema intelligence)
- **LLM** = translator (reads question + skill semantics + MCP schema → generates SQL)

This separates concerns cleanly: business rules live in SKILL.md files, while the MCP handles actual DB connectivity and query execution.

### Prerequisites
- Docker OR Python 3.12+ with pipx/uv
- PostgreSQL extensions (optional): `pg_stat_statements`, `hypopg` for index tuning and query analysis
