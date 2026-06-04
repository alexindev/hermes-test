# browserless/chrome Source Analysis

This file documents the internal architecture of browserless/chrome relevant to configuring Chrome launch args.

## Key Files (inside container)

| File | Purpose |
|---|---|
| `/usr/src/app/build/config.js` | Config constants — reads `DEFAULT_LAUNCH_ARGS` from env |
| `/usr/src/app/build/chrome-helper.js` | Chrome lifecycle — constructs `puppeteer.launch()` args |
| `/usr/src/app/env.js` | Binary path resolution, docker detection, env exports |
| `/usr/src/app/build/puppeteer-provider.js` | Puppeteer launch provider (alternative path) |
| `/usr/src/app/build/routes.js` | HTTP/WS route handling |

## How `DEFAULT_LAUNCH_ARGS` Reaches Chrome

```
DEFAULT_LAUNCH_ARGS env var
  → config.js:78 (parseJSONParam → exports.DEFAULT_LAUNCH_ARGS)
    → chrome-helper.js:207 (defaultLaunchArgs.args = config_1.DEFAULT_LAUNCH_ARGS)
      → chrome-helper.js:273-278 (convertUrlParamsToLaunchOpts: if URL has --params, replaces defaults)
        → chrome-helper.js:330-339 (launchChrome: [...BROWSERLESS_ARGS, ...opts.args, --remote-debugging-port])
          → puppeteer.launch(finalLaunch)
```

## `BROWSERLESS_ARGS` (always prepended, line 33-39)

```js
const BROWSERLESS_ARGS = [
    '--no-sandbox',
    '--enable-logging',
    '--v1=1',
    '--disable-dev-shm-usage',
    '--no-first-run',
];
```

## Launch args construction (line 335-339)

```js
const launchArgs = Object.assign(Object.assign({}, opts), {
    args: [
        ...BROWSERLESS_ARGS,
        ...(opts.args || []),
        `--remote-debugging-port=${port}`,
    ],
    executablePath: CHROME_BINARY_LOCATION,
    handleSIGINT: false,
    handleSIGTERM: false,
    handleSIGHUP: false,
});
```

## `convertUrlParamsToLaunchOpts` (line 273-328)

URL query params starting with `--` are parsed as Chrome flags. If none are present in the URL, `DEFAULT_LAUNCH_ARGS` from config is used. If any `--` params are in the URL, they replace the default args entirely.

## Verification Commands

```bash
# Dump environment
docker inspect browserless --format '{{json .Config.Env}}' | python3 -m json.tool

# Copy source out for analysis
docker cp browserless:/usr/src/app/build/chrome-helper.js /tmp/
docker cp browserless:/usr/src/app/build/config.js /tmp/

# Search for var usage in built code
docker exec browserless grep -rn "CHROME_FLAGS\|DEFAULT_LAUNCH_ARGS\|BROWSERLESS_ARGS" /usr/src/app/build/

# Check Chrome process args at runtime (only works when a session is active)
docker exec browserless cat /proc/$(docker exec browserless pgrep -f "chrome.*--headless" 2>/dev/null | head -1)/cmdline 2>/dev/null | tr '\0' ' ' || echo "no active chrome"
```

## Env Vars That Do NOT Exist in browserless/chrome

- `CHROME_FLAGS` — common misconception, **not read anywhere**
- `PUPPETEER_ARGS` — not read directly by browserless wrapper