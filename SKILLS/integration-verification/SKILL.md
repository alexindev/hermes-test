---
name: integration-verification
title: System Integration Verification
description: Quick parallel check of all connected systems (DB, Confluence, Jira, NetBox, GitHub, SSH). Use after restarts or when connectivity is uncertain.
tags: [integration, verification, connectivity, troubleshooting]
---

# Integration Verification

Quick parallel checks to verify all connected systems are working after a restart or when connectivity is uncertain.

## Workflow

Run all checks **in parallel** — each takes 1-3 seconds:

### 1. PostgreSQL (MCP)
```python
mcp_postgres_execute_sql("SELECT current_user, current_database()")
```

### 2. Confluence (MCP Atlassian)
```python
mcp_atlassian_confluence_search(query="space=IODD", limit=1)
```

### 3. Jira (MCP Atlassian)
```python
mcp_atlassian_jira_search(jql="project=IODD ORDER BY updated DESC", limit=1)
```

### 4. NetBox (MCP NetBox)
```python
mcp_netbox_netbox_get_objects(object_type="dcim.site", filters={"slug": "dataline"}, limit=1, fields=["id", "name", "status"])
```

### 5. GitHub (gh CLI)
```bash
gh auth status 2>&1; echo "---"; gh repo list alexindev --limit 1
```

### 6. SSH (remote server)
```bash
ssh -i /tmp/hermes-ssh/id_ed25519 -o ConnectTimeout=5 -o StrictHostKeyChecking=no user@host "hostname; uptime"
```

## Results Table Format

Present results as a compact table:

| System | Status | Details |
|--------|--------|---------|
| PostgreSQL | ✅ | DB `bigdata`, user `postgres` |
| Confluence | ✅ | Space `IODD` accessible |
| Jira | ✅ | Project `IODD`, 383 issues |
| NetBox | ✅ | Site `Dataline` active |
| GitHub | ✅ | Auth as `alexindev` |
| SSH | ⚠️ | Key issue: ... |

## Pitfalls

1. **SSH keys are in `/tmp/hermes-ssh/`** — NOT `~/.ssh/`. Container user has no SSH directory.
2. **Confluence search may return empty** for vague queries — use `space=<key>` or specific page titles.
3. **GitHub PAT** — use classic PAT (`ghp_`), not fine-grained (`github_pat_`) which can fail with 403 on push.
4. **NetBox prefix lookup** — use exact match `{"prefix": "10.8.123.0/24"}` not substring match for reliable results.
5. **Run checks in parallel** — don't chain them sequentially, each is independent.

## Common Failure Modes

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| All MCP tools timeout | MCP server container down | Check Docker containers running |
| `gh auth status` fails | Token expired | `gh auth login` |
| SSH "Permission denied" | Wrong key or key not on target | Verify `/tmp/hermes-ssh/id_ed25519.pub` matches target's authorized_keys |
| Confluence returns [] | Query too vague | Use `space=` filter or exact title |
| NetBox returns 0 results | Object type typo | Check valid object_types list in MCP docs |
