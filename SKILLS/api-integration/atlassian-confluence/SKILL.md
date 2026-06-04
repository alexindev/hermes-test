---
name: atlassian-confluence
description: "Connect Hermes Agent to Atlassian Confluence and Jira via MCP — search, read, create, and manage pages and issues. Covers mcp-atlassian setup, CQL/JQL patterns, auth quirks for Server/DC, RAG/semantic search with pgvector, and large-page handling."
version: 1.3.0
author: Hermes Agent
tags: [confluence, jira, atlassian, mcp, knowledge-base, rag, semantic-search]
---

# Atlassian Integration (Confluence + Jira)

Connect Hermes Agent to Atlassian products via the `mcp-atlassian` MCP server (72 tools: Confluence + Jira). Supports both **Cloud** (atlassian.net) and **Server/Data Center** deployments.

## Quick Start

### 1. Install mcp-atlassian

The most complete MCP server for Atlassian (72 tools: Confluence + Jira). Python-based, runs via `uvx`:

```bash
# Verify uvx is available
which uvx || pip install uvx
```

### 2. Get API Credentials

**For Cloud (atlassian.net):**
- Go to https://id.atlassian.com/manage-profile/security/api-tokens
- Create an API token
- Your email is the username

**For Server/Data Center:**
- Create a Personal Access Token (PAT) in Confluence: Profile → Settings → Personal Access Tokens
- PAT authenticates via `Authorization: Bearer <token>` header (not Basic auth, not username+password combo)
- No username required — the token itself identifies the user

### 3. Configure in Hermes Agent

Two formats work — **env vars** (simpler) or **CLI args** (more explicit, useful when both Confluence + Jira are needed).

**Option A: Env vars (works for both Confluence and Jira)**
```yaml
mcp_servers:
  atlassian:
    command: "uvx"
    args: ["mcp-atlassian"]
    env:
      CONFLUENCE_URL: "https://your-company.atlassian.net/wiki"
      CONFLUENCE_USERNAME: "your.email@company.com"
      CONFLUENCE_API_TOKEN: "your_api_token"
      # Jira (optional — same MCP server)
      JIRA_URL: "https://your-company.atlassian.net"
      JIRA_USERNAME: "your.email@company.com"
      JIRA_API_TOKEN: "your_api_token"
```

**Option B: CLI args (both services)**
```yaml
mcp_servers:
  atlassian:
    command: uvx
    args:
      - mcp-atlassian
      - --confluence-url
      - "https://wiki.ucb.local"
      - --confluence-personal-token
      - "your_pat"
      - --no-confluence-ssl-verify     # self-signed certs
      - --jira-url
      - "https://jira.ucb.local"
      - --jira-username
      - "your_username"
      - --jira-token
      - "your_password_or_token"
      - --no-jira-ssl-verify            # self-signed certs
```

For Confluence Server/DC: use `CONFLUENCE_PERSONAL_TOKEN` (or `--confluence-personal-token`) instead of username+token.

Restart Hermes Agent. Tools appear with prefixes `mcp_atlassian_confluence_*` and `mcp_atlassian_jira_*`.

### 4. Available Confluence Tools

| Tool | Description |
|------|-------------|
| `confluence_search` | Search with CQL (Confluence Query Language) |
| `confluence_get_page` | Get page content by ID |
| `confluence_get_page_children` | Get child pages (page tree) |
| `confluence_get_page_history` | Version history |
| `confluence_get_page_diff` | Diff between versions |
| `confluence_create_page` | Create new page |
| `confluence_update_page` | Update existing page |
| `confluence_move_page` | Move/reparent page |
| `confluence_delete_page` | Delete page |
| `confluence_get_comments` | List comments |
| `confluence_add_comment` | Add comment |
| `confluence_reply_to_comment` | Reply to comment |
| `confluence_get_labels` | Get page labels |
| `confluence_add_label` | Add label |
| `confluence_get_attachments` | List attachments |
| `confluence_upload_attachment` | Upload file |
| `confluence_download_attachment` | Download file |
| `confluence_get_page_views` | View analytics |
| `confluence_search_user` | Find Confluence users |

### 5. Available Jira Tools

| Tool | Description |
|------|-------------|
| `jira_search` | Search issues with JQL |
| `jira_get_issue` | Get issue details (fields, changelog, transitions) |
| `jira_create_issue` | Create issue (Task, Bug, Story, Epic, Subtask) |
| `jira_update_issue` | Update fields, add attachments |
| `jira_transition_issue` | Change status (requires transition_id from get_transitions) |
| `jira_add_comment` / `jira_edit_comment` | Comments |
| `jira_get_transitions` | List available status transitions |
| `jira_search_fields` | Find custom field IDs (sprint, story points, etc.) |
| `jira_get_agile_boards` | List Scrum/Kanban boards |
| `jira_get_sprints_from_board` | List sprints on a board |
| `jira_get_sprint_issues` | Issues in a specific sprint |
| `jira_link_to_epic` | Link issue to epic |
| `jira_get_issue_dates` | SLA / cycle time metrics |

### 6. JQL Search Examples

JQL (Jira Query Language) is the native search syntax:

```
# Your unresolved tasks
jira_search(jql="assignee = currentUser() AND resolution = Unresolved")

# Issues in an epic
jira_search(jql="\"Epic Link\" = PROJ-123")

# Issues in a sprint (use customfield_10101 or by sprint ID)
jira_search(jql="Sprint = 10001")

# Find epic children — use "Epic Link" field name
jira_search(jql="\"Epic Link\" = PROJ-471")

# Sprint field tool: search_fields(keyword="sprint") → customfield_10101
```

### 6. CQL Search Examples

CQL (Confluence Query Language) is the native search syntax:

```
# Text search (title + body)
confluence_search(query="onboarding")

# Space-specific
confluence_search(query="space=ENG AND type=page")

# By label
confluence_search(query="label=documentation")

# By contributor
confluence_search(query="contributor=currentUser()")

# Combined
confluence_search(query="text~\"deployment\" AND space=OPS AND lastModified>=2025-01-01")
```

Use `confluence_get_page` after search to retrieve full content.

## Architecture: CQL vs Semantic Search

### Level 1: CQL Search (minimal effort)
Agent searches via CQL, retrieves pages, and synthesizes answers. No infrastructure beyond mcp-atlassian.

**When to use:** Quick knowledge retrieval, exact keyword matching is sufficient.

### Level 2: Agent-Assisted Search (pseudo-semantic)
Agent searches CQL broadly, fetches multiple candidate pages, reads their content, and selects the most relevant ones. LLM reasoning bridges semantic gaps.

**When to use:** Need better than keyword search but don't want to build RAG infrastructure yet.

### Level 3: Full RAG with pgvector (true semantic search)
Full pipeline: Confluence API → chunking → embeddings → pgvector → semantic retrieval → LLM answer.

```
User Query
    │
    ▼
[Embedding Model] ──→ query vector
    │
    ▼
[pgvector] ──→ cosine similarity search
    │
    ▼
[Top-K Chunks] ──→ context + LLM ──→ answer with citations
```

**Components needed:**
1. **Confluence access** (mcp-atlassian or direct REST API)
2. **PostgreSQL + pgvector** — requires `CREATE EXTENSION vector;` (check with `SELECT * FROM pg_available_extensions WHERE name = 'vector'`)
3. **Embedding model** — OpenRouter (`text-embedding-3-small`, `text-embedding-ada-002`) or local vLLM
4. **Chunking + indexing service** — Python MCP server or cronjob
5. **Periodic re-indexing** — cronjob to sync changed pages

## Pre-flight: Test Access with curl Before MCP Setup

Before configuring mcp-atlassian, verify connectivity and auth with curl:

```bash
# Test SSL / reachability first
curl -sk -o /dev/null -w "%{http_code}" https://confluence.your-company.com/rest/api/space \
  -H "Authorization: Bearer YOUR_PAT"

# 000 = SSL error (add -k if self-signed, or configure cert)
# 401 = bad auth
# 200 = OK

# Check which user the PAT belongs to
curl -sk https://confluence.your-company.com/rest/api/user/current \
  -H "Authorization: Bearer YOUR_PAT" | python3 -m json.tool

# Returns: { "username": "...", "displayName": "..." }
```

This confirms:
- The correct auth method (Server/DC uses `Authorization: Bearer <PAT>`, NOT Basic auth)
- The PAT works and which user it belongs to
- Whether SSL needs special handling (self-signed certificates)

## Pitfalls

### Large Pages Get Truncated by MCP Tools

Confluence pages >100KB are truncated by `confluence_get_page` / `confluence_get_page_history`. The page appears to load but content cuts off mid-section.

**Detection:** If returned content ends abruptly or expected sections are missing, the page is too large.

**Workaround — use browser for full reading:**
```bash
browser_navigate("https://wiki.ucb.local/pages/viewpage.action?pageId=<ID>")
browser_snapshot(full=true)   # gets full accessibility tree
```

**Workaround — read saved content via file:**
When MCP returns truncated content, it saves to `/tmp/hermes-results/`. Use `read_file` to access the full output.

**Workaround — section-by-section:**
Use `confluence_get_page_diff` to understand what changed between versions, or navigate to child pages (`confluence_get_page_children`) to break up the content.

### Architecture Review — Spotting Templates vs Real Content

Confluence architecture docs often use template patterns with empty tables. Key signals that a page is NOT actually filled:
- All table rows have empty cells (`|  |  |  |  |`)
- Placeholder text like "Пример:", "incomplete", "46 incomplete"
- Section headers exist but no content below them
- Missing sections (e.g., jumps from 3 directly to 5, skipping 4)
- Date fields empty even though version number exists
- `pageapproval` macro present but zero comments and no approver names listed

**Always verify:** Check for actual data vs template placeholders before concluding an architecture is documented.

### SSL Verification — Self-Signed Certificates (Server/DC)
Most on-premise Confluence instances use self-signed or internal CA certificates. The `mcp-atlassian` Python client (via httpx/requests) will reject them by default.

**Fix:** Add `CONFLUENCE_SSL_VERIFY: "false"` to the MCP server env config:
```yaml
env:
  CONFLUENCE_URL: "https://wiki.ucb.local"
  CONFLUENCE_PERSONAL_TOKEN: "your_pat"
  CONFLUENCE_SSL_VERIFY: "false"    # ← required for self-signed certs
```

Without this, the MCP server connects to the HTTP transport (uvx starts fine) but every tool call fails with `SSLCertVerificationError`.

### Read-Only Mode
When writing tools are disabled via `READ_ONLY_MODE=true` in mcp-atlassian, only read operations (search, get_page, get_comments) remain available.

### Toolset Filtering
Restrict to Confluence-only tools:
```
TOOLSETS=confluence_pages,confluence_comments,confluence_labels,confluence_search
```

### Server/DC Authentication — Confluence
For Server/Data Center, use `CONFLUENCE_PERSONAL_TOKEN` (a PAT), NOT username+API token. Cloud and Server/DC use different auth mechanisms.

PAT authenticates via `Authorization: Bearer <token>` header — no username required.

**URL format:** Server/DC typically uses `https://server-name` (without `/wiki` path suffix), unlike Cloud which needs `https://your-domain.atlassian.net/wiki`.

### Server/DC Authentication — Jira (CRITICAL — version-dependent)
Jira **Server/Data Center** authentication depends on the version:

- **Jira 8.14+** → use `JIRA_PERSONAL_TOKEN` (PAT) — works like Confluence PAT
- **Jira < 8.14** (e.g. 8.10.0) → **PAT is NOT supported** — there is no "Personal Access Tokens" section in the profile

For Jira < 8.14, fall back to **Basic Auth** using `--jira-username` + `--jira-token`:
```yaml
env:
  JIRA_URL: "https://jira.ucb.local"
  JIRA_USERNAME: "aeruslanov"        # your Jira username
  JIRA_TOKEN: "your_password"        # actual password (stored in config.yaml)
  JIRA_SSL_VERIFY: "false"           # self-signed certs
```

Even though the CLI help labels `--jira-username`/`--jira-token` as "for Jira Cloud", they work as **Basic Auth** for Server/DC < 8.14. The password is stored in `config.yaml` on the server — equivalent to storing it in a local `.env` file.

**Pre-flight check — Jira curl before MCP setup:**
```bash
# Verify Basic Auth works
curl -sku "username:password" -o /dev/null -w "%{http_code}" \
  https://jira.your-company.com/rest/api/2/myself
# 200 = OK, 401 = bad credentials, 000 = SSL error

# Get server version (important for auth method)
curl -sk https://jira.your-company.com/rest/api/2/serverInfo | python3 -m json.tool
# → version 8.10.0 → PAT not available → use Basic Auth
```

### pgvector Installation
`CREATE EXTENSION vector` requires superuser access to PostgreSQL. If pgvector is not listed in `pg_available_extensions`, it must be installed at the OS level first (the `postgresql-18-pgvector` package or from source), then created.

### CQL Limitations
CQL is keyword-based and does NOT support semantic search. Misspellings, synonyms, and conceptual queries will miss relevant results. This is the primary motivation for adding pgvector-based RAG.

### NEVER recommend an MCP server without verifying it exists
Always check PyPI/npm/GitHub before suggesting a Confluence MCP server package. mcp-atlassian (`sooperset/mcp-atlassian`) is the verified, maintained option.

### JQL Project Search Limitations

The `~` (contains) operator is NOT supported for the `project` field in JQL. These will all fail:
```
project ~ "WEBUI"        # ❌ FAILS
project ~ "ML"           # ❌ FAILS
```

**Correct approach:** Use exact match `=` or list projects first:
```
jira_search(jql="project = ML")          # ✅ exact match
jira_get_all_projects()                  # ✅ discover keys first
```

When you don't know the project key, call `jira_get_all_projects()` to enumerate available projects, then search with the exact key.

### Jira Subtask Parent Field — String, Not Object

When creating a subtask linked to a parent, the `parent` field in `additional_fields` must be a **plain string**, not a nested object:

```python
# ❌ WRONG — causes "expected 'key' property to be a string" error
additional_fields='{"parent": {"key": "IODD-502"}}'

# ✅ CORRECT — plain issue key string
additional_fields='{"parent": "IODD-502"}'
```

This applies to `jira_create_issue` for subtasks. For epic links, use `epicKey` instead:
```python
additional_fields='{"epicKey": "EPIC-123"}'
```

### Jira Components Must Exist Before Assignment

Components must be pre-created in the project. Attempting to create an issue with a non-existent component fails:
```python
# ❌ Fails if component doesn't exist
components="Open WebUI"

# ✅ Check first with jira_get_project_components
```

If no components exist (empty array from `get_project_components`), omit the `components` parameter entirely.

## References

See `references/` for:
- `references/mcp-atlassian-tools-reference.md` — full 72-tool reference with command signatures
- `references/cql-guide.md` — CQL syntax cheatsheet
- `references/rag-architecture.md` — detailed RAG pipeline design for Confluence
- `references/large-page-handling.md` — strategies for reading oversized Confluence pages
- `references/open-webui-releases.md` — release notes and version tracking for Open WebUI