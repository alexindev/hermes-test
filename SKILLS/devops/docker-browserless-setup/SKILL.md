---
name: docker-browserless-setup
title: Browserless Chrome Docker Setup
description: Configure, run, and debug browserless/chrome Docker containers for browser automation. Covers env vars, Chrome flags, certificate bypass, CDP setup, and container inspection.
tags:
  - browserless
  - docker
  - chrome
  - cdp
  - certificate-errors
  - web-automation
---

# Browserless Chrome Docker Setup

Browserless is a headless Chrome service that exposes a WebSocket (CDP) endpoint for browser automation. It's used to take screenshots, scrape JS-rendered pages, and interact with dynamic websites.

## Quick Start

```bash
docker run -d -p 3000:3000 \
  --shm-size=2gb \
  --name browserless \
  -e DEFAULT_LAUNCH_ARGS='["--ignore-certificate-errors"]' \
  browserless/chrome
```

## Environment Variables

| Variable | Type | Effect | Notes |
|---|---|---|---|
| `DEFAULT_LAUNCH_ARGS` | JSON array | Chrome CLI flags passed to `puppeteer.launch()` | **Use this**, not `CHROME_FLAGS` |
| `CONNECTION_TIMEOUT` | number | WS connection timeout (ms) | Default: 30000 |
| `MAX_CONCURRENT_SESSIONS` | number | Max simultaneous browsers | Default: 10 |
| `TOKEN` | string | API auth token | Optional |
| `PREBOOT_CHROME` | boolean | Pre-warm Chrome instances | Default: false |
| `KEEP_ALIVE` | boolean | Keep browser between requests | Default: false |
| `DEFAULT_HEADLESS` | boolean/string | Headless mode | `true`, `false`, or `'new'` |
| `DEFAULT_BLOCK_ADS` | boolean | Block ads via request interception | Default: false |
| `DEFAULT_STEALTH` | boolean | Enable stealth plugin | Default: false |
| `DEFAULT_IGNORE_HTTPS_ERRORS` | boolean | Puppeteer ignoreHTTPSErrors | Default: false |
| `HOST` | string | Bind address | Default: 0.0.0.0 |
| `PORT` | number | HTTP port | Default: 8080 (overridden to 3000 in docker) |
| `WORKSPACE_DIR` | string | Download/workspace directory | Default: /usr/src/app/workspace |

## The `CHROME_FLAGS` Pitfall (Crucial)

**browserless/chrome does NOT read the `CHROME_FLAGS` env var.** This env var is a common misconception — it exists in some other Docker images but not in browserless.

**Correct approach:** use `DEFAULT_LAUNCH_ARGS` with a JSON array value:

```bash
# ✅ Correct — works
-e DEFAULT_LAUNCH_ARGS='["--ignore-certificate-errors"]'

# ✅ Multiple flags
-e DEFAULT_LAUNCH_ARGS='["--ignore-certificate-errors", "--disable-web-security", "--disable-features=VizDisplayCompositor"]'

# ❌ Wrong — silently ignored
-e CHROME_FLAGS="--ignore-certificate-errors"
```

## Verifying Chrome Args Are Applied

```bash
# Check the env var is set
docker inspect browserless --format '{{json .Config.Env}}' | python3 -m json.tool | grep LAUNCH

# Check Chrome is actually launched with the flag
docker exec browserless ps aux | grep chrome

# If no Chrome process is running (idle), check the source code
docker exec browserless grep -n "DEFAULT_LAUNCH_ARGS\|BROWSERLESS_ARGS" /usr/src/app/build/config.js
```

## How Chrome Args Flow (Source Architecture)

Source: `chrome-helper.js` (compiled in `/usr/src/app/build/`)

1. `config.js:78` reads `DEFAULT_LAUNCH_ARGS` from env as a JSON array
2. `chrome-helper.js:207` sets `defaultLaunchArgs.args` from this config
3. `chrome-helper.js:273-278` — if URL query params start with `--`, they replace the default args
4. `chrome-helper.js:330-339` — `launchChrome()` builds final args: `[...BROWSERLESS_ARGS, ...(opts.args || []), --remote-debugging-port=PORT]`
5. `BROWSERLESS_ARGS` (hardcoded): `['--no-sandbox', '--enable-logging', '--v1=1', '--disable-dev-shm-usage', '--no-first-run']`

## CDP-Based Certificate Error Bypass

Even without restarting the container, you can bypass certificate errors at runtime using CDP:

```python
# After connecting to browserless CDP
await cdp.send("Security.setIgnoreCertificateErrors", {"ignore": True})
```

This is useful when you can't restart the container. Call it once after connecting, before navigating.

## Container Health Check

```bash
# Check if browserless is running
curl -s -o /dev/null -w '%{http_code}' http://host.docker.internal:3000/

# View logs
docker logs browserless --tail 50

# Inspect full environment
docker inspect browserless --format '{{json .Config.Env}}' | python3 -m json.tool
```

## Pitfalls

1. **`CHROME_FLAGS` doesn't exist** — use `DEFAULT_LAUNCH_ARGS` with a JSON array
2. **Idle container has no Chrome process** — browserless only launches Chrome on demand; use source inspection when idle
3. **JSON array quoting** — the env var value must be a valid JSON array: `'["--flag"]'` not `"--flag"`
4. **`--no-sandbox` is already set** — no need to add it, it's in `BROWSERLESS_ARGS`
5. **Certificate errors on corporate/internal sites** — either set `DEFAULT_LAUNCH_ARGS` or use CDP `Security.setIgnoreCertificateErrors`
6. **`--shm-size`** — default shared memory is 64MB, which is too small for Chrome; set `--shm-size=2gb`
7. **Container restarts lose state** — CDP bypass and temp data dirs are ephemeral; changes to `DEFAULT_LAUNCH_ARGS` require container restart

## Reference Files

- `references/source-analysis.md` — Detailed browserless source code analysis, verification commands, and env var reference.

## Related Skills

- `node-inspect-debugger` — for debugging Node.js processes via CDP
- `native-mcp` — for MCP-based tool registration