# VK Teams Platform Integration — Reference

Session-specific details for deploying VK Teams adapter to new Hermes instances.

## Required files

Path: `/opt/data/plugins/vkteams/`

```
adapter.py        (~15KB) — main adapter logic
plugin.yaml       (metadata + env var spec)
__init__.py       (entry point)
```

## Env vars to copy from `.env`

### Mandatory (from `plugin.yaml` requires_env)
| Variable | Purpose |
|----------|---------|
| `VKTEAMS_BOT_TOKEN` | Bot token from Metabot |
| `VKTEAMS_BASE_URL` | API base URL (e.g. `https://api.bki-okb.ru/bot/v1`) |

### Recommended
| Variable | Purpose |
|----------|---------|
| `VKTEAMS_ALLOWED_CHATS` | Comma-separated chat IDs |
| `VKTEAMS_ALLOW_ALL_USERS` | `true` to skip user validation |
| `VKTEAMS_HOME_CHANNEL` | Default chat for cron delivery |

### Optional
| Variable | Purpose |
|----------|---------|
| `VKTEAMS_BOT_MENTION` | Mention string to strip (e.g. `[1000000100]`) |
| `VKTEAMS_CHAT_<id>_SKILL` | Chat→skill mapping |
| `VKTEAMS_HOME_CHANNEL_THREAD_ID` | Thread ID for home channel |

## Config.yaml sections

```yaml
gateway:
  enabled:
    - vkteams

vkteams:
  require_mention: true
```

## Python dependency

Only `requests` — install via:
```bash
/opt/data/hermes-tools/.venv/bin/pip install requests
```

## Known fix: replyMsgId format

VK Teams API spec requires `replyMsgId` as **array of integers**, not scalar.
In `adapter.py`, lines with `replyMsgId` must use:
```python
params['replyMsgId'] = [reply_msg_id]  # NOT: reply_msg_id
```

## Testing after deployment

1. Simple message: send any text to the bot
2. File send: use adapter's `_send_file()` method, NOT curl
3. Reply-to: verify `replyMsgId` is treated as array
