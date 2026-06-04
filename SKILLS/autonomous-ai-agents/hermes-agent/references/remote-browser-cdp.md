# Remote CDP Browser for Hermes

Configure Hermes to use a remote headless Chrome via CDP (Chrome DevTools Protocol) for full JS rendering, CSS, and dynamic content in browser tools.

## When to Use This

- Hermes runs inside a container with no local Chrome (common Docker deployment)
- You need JS rendering for `web_extract` / page snapshots (SPA, React, dynamic content)
- You want self-hosted extraction without paid API keys (Firecrawl, Tavily, etc.)
- **Alternative to:** Firecrawl self-hosted (heavy, ~10 containers) or cloud CDP services

## Architecture

```
Host machine (Docker Desktop, Linux, etc.)
│
├─ Container: browserless/chrome (or any headless Chrome with CDP)
│  Port 3000 → CDP WebSocket: ws://<host>:3000
│
└─ Container: Hermes
   config.yaml → browser.cdp_url = ws://host.docker.internal:3000
```

## Container Options

### Option 1: browserless/chrome (recommended)

Purpose-built for remote CDP. Single container, no extra config.

```bash
docker run -d \
  --name chrome-cdp \
  -p 3000:3000 \
  --shm-size=2gb \
  -e CONNECTION_TIMEOUT=60000 \
  -e MAX_CONCURRENT_SESSIONS=10 \
  -e PREBOOT_CHROME=true \
  -e ENABLE_DEBUG_LOGGING=true \
  -e CHROME_FLAGS="--ignore-certificate-errors" \
  -e DEFAULT_LAUNCH_ARGS='["--ignore-certificate-errors"]' \
  browserless/chrome:latest

**Critical flags:**
- `--shm-size=2gb` — Chrome needs shared memory for rendering. Docker default (64MB) causes silent startup failure (container stays in `Created` state forever).
- `DEFAULT_LAUNCH_ARGS='["--ignore-certificate-errors"]'` — Without this, all HTTPS sites fail with `net::ERR_CERT_AUTHORITY_INVALID` because the container's Chrome doesn't trust the host's root CA bundle.

**Ports:** 3000 (CDP WebSocket)  
**Size:** ~1.5 GB  
**Features:** Concurrent sessions, configurable timeouts

### Option 2: Zenika Alpine Chrome

Lighter (~300 MB) but needs explicit CDP flags.

```bash
docker run -d \
  --name chrome-cdp \
  -p 9222:9222 \
  zenika/alpine-chrome:latest \
  --remote-debugging-port=9222 \
  --remote-debugging-address=0.0.0.0 \
  --headless --no-sandbox --disable-gpu
```

**CDP URL:** `ws://host.docker.internal:9222/devtools/browser/<id>`  
**Note:** You need to fetch the WebSocket URL first via `http://host.docker.internal:9222/json/version`

### Option 3: Playwright

If you already run Playwright, expose its CDP endpoint:

```python
# Just exposing CDP — no extra app needed
browser = await playwright.chromium.launch(
    headless=True,
    args=['--remote-debugging-port=9222', '--remote-debugging-address=0.0.0.0']
)
```

## Hermes Configuration

In `config.yaml`:

```yaml
browser:
  cdp_url: ws://host.docker.internal:3000    # browserless default
  # cdp_url: ws://host.docker.internal:9222  # if using alpine-chrome
  engine: auto                                 # auto-detect CDP vs local
  inactivity_timeout: 120                      # idle session timeout (seconds)
  command_timeout: 30                          # per-command timeout (seconds)
  dialog_policy: must_respond
  dialog_timeout_s: 300
```

Then enable the browser toolset (if not already):

```bash
hermes tools enable browser
```

Apply with `/reset` (new session) or restart the gateway.

## Verification

```bash
# 1. Container is up
docker ps --filter name=chrome-cdp --format "{{.ID}} {{.Status}}"

# 2. CDP WebSocket responds
curl -s http://host.docker.internal:3000/json/version | python3 -c "import sys,json; d=json.load(sys.stdin); print('Chrome:', d.get('Browser','?'))"
# Should print: Chrome: HeadlessChrome/...

# 3. Inside Hermes session
# browser_navigate("https://example.com") → should succeed
# browser_navigate("https://www.google.com") → should load full page with search
```

## Troubleshooting

### Container stuck in `Created` status

The container was pulled from the registry but never actually starts:

```
docker ps --filter name=chrome-cdp
# Status: "Created" (not "Up")
```

**Root causes (in order of likelihood):**

1. **Insufficient Docker Desktop resources** — macOS/Windows Docker Desktop VM needs enough memory. Check with `docker info | grep Memory`. If total < 4GB and several containers run, the daemon can't schedule new containers. Fix: increase Docker Desktop resources (Settings → Resources → Memory → 8GB+) and restart Docker Desktop.

2. **Shared memory too small** — Add `--shm-size=2gb` to the `docker run` command.

3. **Docker daemon overloaded** — Clean up build cache: `docker builder prune -af`

### HTTPS fails with `ERR_CERT_AUTHORITY_INVALID`

Every HTTPS site fails, HTTP works fine. The container's Chrome doesn't trust the OS certificate bundle:

**Fix:** Set `DEFAULT_LAUNCH_ARGS` when creating the container, then recreate (not just restart).

⚠️ **Do NOT use `CHROME_FLAGS`** — this env var is NOT read by browserless/chrome. It was a common mistake. The correct variable is `DEFAULT_LAUNCH_ARGS`, which expects a JSON array of Chrome CLI arguments.

```bash
docker rm -f chrome-cdp
docker run -d ... -e DEFAULT_LAUNCH_ARGS='["--ignore-certificate-errors"]' browserless/chrome
```

**How to verify:** After recreating the container, check the env vars are set correctly:
```bash
docker inspect chrome-cdp --format '{{json .Config.Env}}' | python3 -m json.tool | grep DEFAULT_LAUNCH
# Should show: "DEFAULT_LAUNCH_ARGS=[\"--ignore-certificate-errors\"]"
```

Note: running `docker exec --user root <container> update-ca-certificates` does NOT fix this — Chrome uses its own certificate store, not the system one.

### Config changes don't take effect

After setting/changing `browser.cdp_url` in config.yaml, a new session is required:
- CLI: exit and restart Hermes, or `/reset`
- Gateway: `/restart` or restart the container

The `browser` config section is snapshotted at process startup.

### Docker Desktop on Windows

Use `host.docker.internal` to reach the CDP container from Hermes. On Linux, use `172.17.0.1` (docker bridge) or a custom network.

## Combined Pattern: No API Keys for Web Extraction

This setup + SearXNG = completely self-hosted web stack:

| Tool | Component | Container | 
|------|-----------|-----------|
| `web_search` | SearXNG | `searxng/searxng` (port 8888) |
| `browser_*` | Remote CDP Chrome | `browserless/chrome` (port 3000) |

No paid API keys needed. SearXNG handles search queries; the CDP browser renders any page with full JS for content extraction.