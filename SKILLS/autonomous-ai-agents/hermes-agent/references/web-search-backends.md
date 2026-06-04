# Web Search Backends in Hermes Agent

## Architecture

All 7 web providers live as plugins under `/opt/hermes/plugins/web/<name>/`. They are bundled with Hermes Agent and auto-loaded at startup. No manual installation needed.

### Plugin location
```
/opt/hermes/plugins/web/
├── brave_free/      # Brave Search (free tier)
├── ddgs/            # DuckDuckGo (requires pip install ddgs)
├── exa/             # Exa AI (paid API key)
├── firecrawl/       # Firecrawl (paid + self-hosted)
├── parallel/        # Parallel API (paid)
├── searxng/         # SearXNG (self-hosted, free)
└── tavily/          # Tavily (paid API key)
```

### Registration vs Availability — critical distinction

All 7 providers **auto-register unconditionally** at Hermes startup via `ctx.register_web_search_provider()` in their `__init__.py`. Registration happens regardless of whether API keys exist. This means:

- Every provider is always in the registry (visible via `web_search_registry.list_providers()`)
- An explicitly configured backend (e.g. `web.backend: searxng`) resolves to a **registered name** even if the env var is missing
- `is_available()` controls whether the provider is *usable*, but **does not** affect config-level name resolution

**Pitfall**: `_get_backend()` in `web_tools.py` checks only whether `web.backend` names a known backend string — it returns the configured name unconditionally, ignoring `is_available()`. So `web.backend: searxng` returns `"searxng"` even when `SEARXNG_URL` is unset. The availability check happens later in the actual tool dispatch.

### Activation (making a provider *usable*)

Each provider becomes usable when TWO things are true:

1. **Environment variable** — each provider checks a specific env var:
   | Provider | Env Var | Supports extract? |
   |----------|---------|-------------------|
   | searxng | `SEARXNG_URL` | ❌ (search only) |
   | brave-free | `BRAVE_SEARCH_API_KEY` | ❌ (search only) |
   | ddgs | package importable (no env var) | ❌ (search only) |
   | exa | `EXA_API_KEY` | ✅ |
   | tavily | `TAVILY_API_KEY` | ✅ |
   | parallel | `PARALLEL_API_KEY` | ✅ |
   | firecrawl | `FIRECRAWL_API_KEY` or `FIRECRAWL_API_URL` | ✅ |

2. **Config entry** — set in `config.yaml`:
   ```yaml
   web:
     backend: searxng              # shared fallback for both search + extract
     search_backend: searxng       # per-capability override (search only)
     extract_backend: ""           # per-capability override (extract only)
   ```

### Backend selection priority

For `web_search`:
1. `web.search_backend` (per-capability override)
2. `web.backend` (shared fallback)
3. Auto-detect from available env vars (priority: firecrawl > parallel > tavily > exa > searxng > brave-free > ddgs)

For `web_extract`:
1. `web.extract_backend` (per-capability override)
2. `web.backend` (shared fallback)
3. Auto-detect from available env vars

**⚠️ Important: config-resolution returns a NAME, not a capable provider.**
`_get_extract_backend()` (in `web_tools.py`) resolves to a backend **name** via `_get_capability_backend()` → `_get_backend()`. When `web.backend` is explicitly configured (e.g. `searxng`), `_get_backend()` returns it **unconditionally** — it does NOT check whether the named provider supports extract. The availability/capability check happens later, inside `web_extract_tool()` itself.

### Two-Tier Fallback: Config Resolution vs Runtime

The fallback operates at TWO distinct levels, which is a common source of confusion:

**Tier 1 — Config resolution** (`_get_extract_backend()` in `web_tools.py:181`):
```
web.extract_backend (explicit) → web.backend (shared) → _get_backend() legacy auto-detect
```
Returns a **string name**. Does NOT check capability or even registration — a configured name always wins.

**Tier 2 — Runtime provider resolution** (inside `web_extract_tool()` in `web_tools.py:930`):
```
backend name → _wsp_get_provider(name) → check supports_extract()
    ├── Provider IS registered but search-only → STOPS with error
    └── Provider name not registered (typo/uninstalled) → falls through to
        get_active_extract_provider() → legacy preference walk (firecrawl > ...)
```

This means: when `web.backend: searxng` is configured but SearXNG has no extract capability, the config-layer `_get_extract_backend()` happily returns `"searxng"`. The error surfaces only at the runtime layer inside `web_extract_tool()`. The effective fallback is **not** transparent — the tool returns an error message, it doesn't silently switch providers.

To avoid this, always set `web.extract_backend` explicitly when using SearXNG for search:

```yaml
web:
  search_backend: searxng
  extract_backend: firecrawl      # or tavily / exa / parallel
```

### CRITICAL: OpenAI Native Web Search bypasses all our providers

When the model uses the **OpenAI Responses API** (not the Chat Completions API), it can invoke a **native `web_search` tool** that calls OpenAI's own web search backend directly (Google/Bing via OpenAI infrastructure). This completely bypasses:
- Our plugin registry (`web_search_registry`)
- All 7 configured backends (SearXNG, Brave, Tavily, etc.)
- The `web.backend` / `web.search_backend` config settings

**How to detect:** If `web_search` returns results but your SearXNG instance is down, or if `list_providers()` shows no active providers yet search still works — you're hitting OpenAI Native Web Search, not any configured backend.

**How to disable:** In `config.yaml`, set `model.provider` to a non-OpenAI provider (e.g. `openrouter`, `anthropic`) or use a model that doesn't support native web search. Alternatively, check if the OpenAI provider has a config toggle for native web search (provider-specific).

**Why this matters:** Even with perfect SearXNG config (`SEARXNG_URL` set, `search_backend: searxng`, instance reachable), the model may still use OpenAI's built-in search because the Responses API treats `web_search` as a first-class tool. Our entire plugin chain is invisible to it.

## Quick Setup: SearXNG

1. Add to `~/.hermes/.env`:
   ```
   SEARXNG_URL=http://host.docker.internal:8888
   ```

2. Add to `~/.hermes/config.yaml` under `web:`:
   ```yaml
   search_backend: searxng
   ```

3. `/reset` to reload (config is snapshotted at session start).

## Troubleshooting

### `web.search_backend` is set but `web_search` returns "No provider" or falls back to another backend

**Most common cause:** `SEARXNG_URL` env var is empty inside the container.

Diagnostic:
```bash
python3 -c "import os; print('SEARXNG_URL:', repr(os.environ.get('SEARXNG_URL','<NOT_SET>')))"
```

⚠️ **Do NOT use `echo "SEARXNG_URL=$SEARXNG_URL"` for diagnostics.** Hermes' display-layer secret-masking intercepts patterns like `VAR=value` and replaces them with `***`, so you can't distinguish between a missing var and a set-but-masked one. Use `python3 -c "import os; print(repr(os.environ.get('VAR','<NOT_SET>')))"` instead, which avoids the pattern-matching because the output shape is `'VALUE'` not `VAR=VALUE`.

Also reliable: `printenv | grep VAR` — but `printenv` exits 1 and produces no output on no match, which may look like an empty result.

The provider's `is_available()` checks `os.getenv("SEARXNG_URL", "").strip()` — if empty, the provider is marked unavailable and `web_search` silently falls through to the next available backend (or errors).

Fix:
1. Add `SEARXNG_URL=http://host.docker.internal:8888` (or your instance URL) to `~/.hermes/.env`
2. Or export it in the container: `docker exec <container> env | grep SEARXNG` to check, then fix docker-compose / run args
3. `/reset` — config and env vars are snapshotted at session start

### SearXNG instance not reachable

If `SEARXNG_URL` is set but requests time out:
```bash
curl -s --connect-timeout 3 "http://<url>/search?q=test&format=json" | head -c 200
```
Inside a Docker container, use `host.docker.internal` to reach services on the host machine. If the container uses a custom Docker network, use the container name or service name as hostname instead of `host.docker.internal`.

### Debugging the full web_search dispatch chain

When `web_search` behaves unexpectedly, trace through these layers:

1. **Config**: `grep -A 5 "^web:" ~/.hermes/config.yaml` — check `backend`, `search_backend`, `extract_backend`
2. **Env vars**: `echo "SEARXNG_URL=$SEARXNG_URL"` — each provider needs its specific env var
3. **Registry**: The dispatch goes `web_search_tool()` → `_get_search_backend()` → `web_search_registry._resolve()` → provider's `search()` method
4. **HTTP call**: Provider uses `httpx.get()` with 15s timeout against `{SEARXNG_URL}/search?format=json&q=<query>`

### Quick diagnostic — full provider health check

Run this to see which providers are registered vs actually usable:

```python
python3 -c "
import os
checks = [
    ('firecrawl',   'FIRECRAWL_API_KEY',     bool(os.environ.get('FIRECRAWL_API_KEY') or os.environ.get('FIRECRAWL_API_URL'))),
    ('parallel',    'PARALLEL_API_KEY',      bool(os.environ.get('PARALLEL_API_KEY'))),
    ('tavily',      'TAVILY_API_KEY',        bool(os.environ.get('TAVILY_API_KEY'))),
    ('exa',         'EXA_API_KEY',           bool(os.environ.get('EXA_API_KEY'))),
    ('searxng',     'SEARXNG_URL',           bool(os.environ.get('SEARXNG_URL'))),
    ('brave-free',  'BRAVE_SEARCH_API_KEY',  bool(os.environ.get('BRAVE_SEARCH_API_KEY'))),
    ('ddgs',        'ddgs package',          __import__('importlib').util.find_spec('ddgs') is not None),
]
for name, env_var, available in checks:
    status = '✅ usable' if available else '❌ no credentials'
    print(f'{name:14s} {status}  ({env_var})')
"
```

This is tested with the rest of the diagnostics section.

Source locations:
- Dispatch logic: `/opt/hermes/tools/web_tools.py::web_search_tool()` (line ~736)
- Registry: `/opt/hermes/agent/web_search_registry.py`
- SearXNG provider: `/opt/hermes/plugins/web/searxng/provider.py`
- Firecrawl provider: `/opt/hermes/plugins/web/firecrawl/provider.py`
- Provider registrations: `/opt/hermes/plugins/web/<name>/__init__.py::register()`

- **Plugin not appearing**: Check that the env var is set AND the config entry matches exactly (`searxng`, not `SearXNG`). Case-sensitive.
- **Auto-detect picked wrong provider**: Set `web.search_backend` explicitly to override auto-detection priority.
- **web_extract fails after setting searxng**: Expected — SearXNG has no extract capability. Set `extract_backend` to a different provider.
- **web_extract error "SearXNG is a search-only backend"**: This means `web.backend` or `web.search_backend` is `searxng` but no `extract_backend` is configured. The code resolves the backend name at the config layer (returns `"searxng"`), then at runtime checks `supports_extract()` → False → returns this error. Fix: set `web.extract_backend` explicitly (or remove `web.backend` and configure both `search_backend` + `extract_backend` separately).
- **Plugin files missing**: Reinstall Hermes Agent — plugins ship with source code, not installed separately.
