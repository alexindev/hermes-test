# VK Teams Platform Adapter for Hermes Agent

## Overview
This plugin provides a native platform adapter for VK Teams corporate messenger.
It enables Hermes Agent to receive and send messages via VK Teams Bot API.

## Files
- `adapter.py` — Main platform adapter (377 lines)
- `plugin.yaml` — Plugin manifest with env var definitions
- `__init__.py` — Plugin entry point

## Installation

1. Copy the `vk-teams/` directory to your Hermes Agent plugins path:
   ```bash
   cp -r vk-teams /opt/data/plugins/vkteams
   ```

2. Restart the Hermes Agent gateway:
   ```bash
   hermes gateway restart
   ```

## Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VKTEAMS_BOT_TOKEN` | Bot token from Metabot | `001.08xxxxx0100` |
| `VKTEAMS_BASE_URL` | VK Teams API base URL | `https://api.bki-okb.ru/bot/v1` |

### Optional Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VKTEAMS_ALLOWED_CHATS` | Comma-separated list of allowed chatIds | `107756@chat.agent,107890@chat.agent` |
| `VKTEAMS_ALLOWED_USERS` | Comma-separated list of allowed userIds | |
| `VKTEAMS_ALLOW_ALL_USERS` | Set to `true` to allow all users | `true` |
| `VKTEAMS_HOME_CHANNEL` | Default chat_id for cron delivery | `107756@chat.agent` |
| `VKTEAMS_BOT_MENTION` | Mention string to strip from messages | `[1000000100]` |
| `VKTEAMS_POLL_TIME` | Long-poll wait time in seconds | `30` |

### Chat-Specific Skills

Use `VKTEAMS_CHAT_<sanitized_chat_id>_SKILL` to assign skills per chat:

```bash
# Chat 107890@chat.agent -> sanitized: 107890_chat_agent
export VKTEAMS_CHAT_107890_chat_agent_SKILL="database-postgres"
```

## How It Works

1. **Polling**: The adapter runs a background thread that polls VK Teams API for new events using long-polling.
2. **Message Routing**: Incoming messages are filtered by allowed chats and mention requirements.
3. **Skill Assignment**: Messages can be routed to different skills based on the chat ID.
4. **Reply**: Responses are sent back via VK Teams API (text chunked at 4000 chars, files uploaded via multipart).

## Features

- ✅ Text messages (auto-chunked at 4000 chars)
- ✅ File uploads (multipart/form-data)
- ✅ File resend by fileId (no re-upload)
- ✅ Image support
- ✅ Reply-to-message support
- ✅ Per-chat skill routing
- ✅ Mention-based activation
- ✅ Allowed chats/users filtering

## Dependencies

- `requests` — HTTP client (already bundled with Hermes Agent)
- No additional pip packages required
