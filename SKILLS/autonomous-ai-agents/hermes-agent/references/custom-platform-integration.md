# Custom Messaging Platform Integration

Hermes supports two patterns for non-native platforms:

## Pattern A: API Server + Proxy Script (legacy / lightweight)

Use when you just need a bridge and don't need full Hermes tool access on the platform.

```
Platform Users  ←→  Platform Bot API  ←→  Proxy Script  ←→  Hermes API Server (:8642)
```

The proxy:
1. Polls/receives events from the platform's Bot API
2. Formats messages as OpenAI-compatible JSON
3. Sends to `POST /v1/chat/completions` on Hermes API Server
4. Receives response and sends back via platform's send endpoint

### Pitfalls
- **Self-hosted vs SaaS**: Different API URLs for self-hosted instances — check actual base URL, not public docs.
- **Long-polling vs webhooks**: Prefer webhooks if available (lower latency).
- **Session continuity**: Pass conversation history in `messages` array, not just `user` content.
- **Token auth**: Many platforms put auth tokens in query params, not headers.
- **SSL/TLS**: Self-hosted APIs may use self-signed certs — disable verification if needed.

## Pattern B: Platform Plugin Adapter (full Hermes integration)

Use when you want the platform to have full Hermes tool access (terminal, file, search, etc.) — the adapter registers as a native gateway platform.

### Architecture

```
Platform Users  ←→  Platform Bot API  ←→  Plugin Adapter (threaded poller)  ←→  Hermes Gateway Runner
```

The adapter runs inside the Hermes gateway process as a registered platform — same lifecycle as Telegram/Discord adapters.

### Directory Layout

```
$HERMES_HOME/plugins/<name>/
├── plugin.yaml          # Manifest (required)
├── __init__.py          # Must import and re-export `register`
└── adapter.py           # PlatformAdapter implementation
```

`HERMES_HOME` defaults to `/opt/data` on Linux. The gateway scans `$HERMES_HOME/plugins/` during startup via `discover_plugins()`.

### plugin.yaml Schema

```yaml
name: <platform_name>              # Unique identifier, used as platform key
label: <Display Name>              # Human-readable name
kind: platform                     # MUST be "platform" for gateway adapters
version: 1.0.0
description: <one-liner>
author: <author>
requires_env:                      # Required env vars (triggers install_hint if missing)
  - name: PLATFORM_TOKEN
    description: "Bot token"
    prompt: "Platform Token"
    password: true
optional_env:                      # Optional env vars
  - name: PLATFORM_ALLOWED_USERS
    description: "Comma-separated allowed user IDs"
    password: false
  - name: PLATFORM_HOME_CHANNEL
    description: "Default chat_id for cron delivery"
    password: false
```

### adapter.py — Required Functions

Three top-level functions MUST be exported:

1. **`check_requirements() -> bool`** — Called at gateway startup. Returns True if the platform can be loaded. Reads env vars, returns False if missing.

2. **`validate_config(config) -> bool`** — Validates the runtime config object.

3. **`register(ctx)`** — Called by the plugin manager. Invokes `ctx.register_platform(...)` with all metadata.

### adapter.py — PlatformAdapter Class

Inherit from `BasePlatformAdapter` and implement:

```python
from gateway.platforms.base import BasePlatformAdapter, MessageEvent, MessageType, SendResult

class MyAdapter(BasePlatformAdapter):
    def __init__(self, config: PlatformConfig):
        super().__init__(config, Platform('myplatform'))  # ← CRITICAL: see pitfalls below
        # Read config from os.environ or config.extra
    
    async def connect(self) -> bool:
        # Start polling thread, mark connected
        return True
    
    async def disconnect(self) -> None:
        # Stop polling, mark disconnected
    
    async def send(self, chat_id, content, reply_to=None, metadata=None):
        # Send message via platform API
        return SendResult(success=True, message_id="...")
    
    async def get_chat_info(self, chat_id):
        return {'name': chat_id, 'type': 'group'}
```

### ctx.register_platform() Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Platform key (must match plugin.yaml `name`) |
| `label` | str | Display name |
| `adapter_factory` | callable | `lambda cfg: MyAdapter(cfg)` |
| `check_fn` | callable | `check_requirements` |
| `validate_config` | callable | `validate_config` |
| `required_env` | list[str] | Env var names for allowlist detection |
| `install_hint` | str | Shown if requirements not met |
| `env_enablement_fn` | callable | Returns dict with token, base_url, home_channel, bot_mention |
| `cron_deliver_env_var` | str | Env var for cron delivery target (e.g. `MY_PLATFORM_HOME_CHANNEL`) |
| `allowed_users_env` | str | Env var for user allowlist (e.g. `MY_PLATFORM_ALLOWED_USERS`) |
| `allow_all_env` | str | Env var to allow all users (e.g. `MY_PLATFORM_ALLOW_ALL_USERS`) |
| `max_message_length` | int | Max chars per message |
| `platform_hint` | str | System prompt prefix for this platform |
| `emoji` | str | Emoji for UI display |

### Pitfalls

- **Platform enum mismatch**: `Platform('myplatform')` will raise `ValueError` if `'myplatform'` is not in the built-in `Platform` enum. The gateway checks `platform_registry.is_registered(platform.value)` — if the value isn't recognized, the adapter won't start. Workaround: the adapter class constructor passes the string to `Platform()`, which validates against the enum. You need to ensure the platform name matches a registered enum value OR patch the enum.

- **MessageEvent platform field**: When constructing `MessageEvent`, the `platform` parameter should match the same value used in `super().__init__()`. Using a bare string like `platform='myplatform'` may bypass enum validation but could cause issues in gateway routing logic.

- **`asyncio.get_event_loop()` deprecation**: On Python 3.10+, `asyncio.get_event_loop()` in a non-async context emits DeprecationWarning. Use `asyncio.new_event_loop()` + `asyncio.set_event_loop()` instead.

- **Polling thread safety**: The poll loop runs in a background thread. Use `asyncio.run_coroutine_threadsafe(fn, self._loop)` to dispatch events to the gateway's event loop. Store `self._loop = asyncio.get_event_loop()` in `connect()`.

- **Allowlist detection**: Gateway auto-detects plugin allowlists via `platform_registry.plugin_entries()`. Your `register_platform` call MUST set `allowed_users_env` and `allow_all_env` — otherwise the gateway won't know which env vars to check and will deny all users (unless `GATEWAY_ALLOW_ALL_USERS=true`).

- **Cron delivery**: Set `cron_deliver_env_var` to the env var name (e.g. `MY_PLATFORM_HOME_CHANNEL`). The gateway uses this to resolve the delivery target for cron jobs. Without it, cron delivery to this platform won't work.

- **Bot mention filtering**: If your platform requires @mention filtering, do it in `_dispatch()` before creating the `MessageEvent`. Strip the mention from text after checking.

### Example: VK Teams Plugin (session 2026-05-27)

VK Teams corporate adapter at `/opt/data/plugins/vkteams/`:
- Uses `requests` (not `aiohttp`) — required for corporate api.bki-okb.ru deployments
- Polls `GET /events/get?lastEventId=N&pollTime=30&token=TOKEN` in a background thread
- Dispatches via `asyncio.run_coroutine_threadsafe(self.handle_message(msg_event), self._loop)`
- Filters on `newMessage` events only, checks `bot_mention` in text
- Uses `VKTEAMS_BOT_MENTION` env var for @mention filtering (e.g. `[1000000100]`)
- Token format: `001.<server_id>.<client_id>:<secret>`
- Chat ID format: `<group_id>@chat.agent`
- `VKTEAMS_POLL_TIME` controls polling interval (default 30s)

### VK Teams Corporate Deployment Notes

- Server `api.bki-okb.ru` blocks incoming events for bots — `sendText` works (outgoing), but `events/get` always returns empty for bot-sent messages
- Messages sent BY the bot do NOT appear in events stream — this is expected behavior, no self-loop risk
- Only `newMessage` events from actual users reach the adapter
- Use `VKTEAMS_BOT_MENTION` to filter only messages that mention the bot
- Never use `"hermes-internal-key"` as API key — it's a placeholder
