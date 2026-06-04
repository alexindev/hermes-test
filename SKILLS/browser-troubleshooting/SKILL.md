---
name: browser-troubleshooting
description: Common issues when working with headless browsers (browserless, Playwright, Puppeteer) in Hermes Agent sessions — config fixes, SSL errors, and debugging patterns.
category: devops
---

# Browser Troubleshooting

Common issues when working with headless browsers (browserless, Playwright, Puppeteer) in Hermes Agent sessions.

## browserless Docker Container Configuration

### Pitfall: `CHROME_FLAGS` is NOT read by browserless

The `CHROME_FLAGS` environment variable is a common misconception — it does NOT appear anywhere in the browserless source code (`/usr/src/app/build/`). Setting it via docker run has zero effect.

**Wrong:**
```bash
docker run -e CHROME_FLAGS="--ignore-certificate-errors" browserless/chrome
```

**Correct — use `DEFAULT_LAUNCH_ARGS`:**
```bash
docker run -e 'DEFAULT_LAUNCH_ARGS=["--ignore-certificate-errors"]' browserless/chrome
```

`DEFAULT_LAUNCH_ARGS` is read by `config.js` line 78 and passed to Chrome at launch.

### How to verify which env vars browserless actually uses

1. Copy relevant files from the container:
   ```bash
   docker cp <container>:/usr/src/app/build/config.js /tmp/config.js
   docker cp <container>:/usr/src/app/build/chrome-helper.js /tmp/chrome-helper.js
   ```
2. Search for the variable name:
   ```bash
   grep -rn "VARIABLE_NAME" /tmp/*.js
   ```
3. If nothing found → the env var is ignored.

### Common browserless env vars that DO work

| Variable | Purpose | Format |
|----------|---------|--------|
| `DEFAULT_LAUNCH_ARGS` | Chrome launch args | JSON array string: `'["--arg1","--arg2"]'` |
| `CONNECTION_TIMEOUT` | Session timeout (ms) | Integer |
| `MAX_CONCURRENT_SESSIONS` | Max parallel browsers | Integer |
| `HEADLESS` | Default headless mode | Boolean/string |
| `PORT` | HTTP port | Integer |

### SSL certificate errors

If pages fail with `NET::ERR_CERT_AUTHORITY_INVALID`:
1. Fix it at the browserless level with `--ignore-certificate-errors` in `DEFAULT_LAUNCH_ARGS`
2. As a quick workaround, use CDP: `Security.setIgnoreCertificateErrors` → `{"ignore": true}`

## Generic debugging approach

When a browser tool fails unexpectedly:
1. Check the container/service is running: `docker ps --filter name=browserless`
2. Verify env vars actually exist in the container: `docker inspect <name> --format '{{json .Config.Env}}'`
3. Search the source code for the variable — don't assume env var names match CLI flags
4. Test connectivity: `curl -s -o /dev/null -w '%{http_code}' http://host.docker.internal:3000/`