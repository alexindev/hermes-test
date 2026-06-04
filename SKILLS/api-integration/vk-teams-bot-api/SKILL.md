---
name: vk-teams-bot-api
description: VK Teams Bot API integration — sending files, images, text messages, and polling events via the corporate bot API endpoint.
---

# VK Teams Bot API

Integration with VK Teams (formerly ICQ) Bot API for sending messages and files from Hermes Agent.

## Configuration

VK Teams adapter is configured via environment variables (in `/opt/data/.env`):

| Variable | Purpose |
|---|---|
| `VKTEAMS_BOT_TOKEN` | Bot secret token |
| `VKTEAMS_BASE_URL` | Corporate API endpoint (e.g. `https://api.bki-okb.ru/bot/v1`) |
| `VKTEAMS_BOT_MENTION` | Bot mention string (e.g. `[1000000100]`) |
| `VKTEAMS_ALLOWED_CHATS` | Comma-separated list of allowed chat IDs |
| `VKTEAMS_HOME_CHANNEL` | Default home channel chat ID |

Chat ID format: `107756@chat.agent` (numerical ID + `@chat.agent` suffix).

## Sending Images/Screenshots to VK Teams

### Direct API call (required for all media in VK Teams)

VK Teams does NOT support `MEDIA:` prefix via the `send_message` tool — the platform only supports media attachments through its own API endpoints. Use direct `curl` calls or the adapter's `_send_file` method.

**Upload + send (multipart/form-data):**
```bash
curl -s -X POST \
  "${VKTEAMS_BASE_URL}/messages/sendFile?token=${VKTEAMS_BOT_TOKEN}&chatId=CHAT_ID&caption=TEXT" \
  -F "file=@/path/to/file.png"
```

**Resend by fileId (no upload needed):**
```bash
curl -s -X GET \
  "${VKTEAMS_BASE_URL}/messages/sendFile?token=${VKTEAMS_BOT_TOKEN}&chatId=CHAT_ID&fileId=FILE_ID&caption=TEXT"
```

**Success response:**
```json
{"ok": true, "fileId": "095ZZ000TtlH6wZbnjgE9x6a214bc11af", "msgId": "7647476934552585664"}
```

### Adapter override (for programmatic sending from Python)

The base `BasePlatformAdapter.send_document()` and `send_image_file()` fall back to sending file paths as plain text. Override them in `/opt/data/plugins/vkteams/adapter.py`:

Use when you need to send a pre-existing file without going through the response pipeline.

```bash
curl -s -X POST \
  "${VKTEAMS_BASE_URL}/messages/sendFile?token=${VKTEAMS_BOT_TOKEN}&chatId=CHAT_ID&caption=TEXT" \
  -F "file=@/path/to/file.png;type=image/png;filename=name.png"
```

#### curl modes

1. **POST (upload + send)** — send `file` as multipart/form-data binary. Use for first-time sends.
2. **GET (resend by fileId)** — pass `fileId` from a previous upload response. Cheaper, no upload needed.

#### Success response

```json
{
  "ok": true,
  "fileId": "0cU9G000PBjXrhbLxrRVrD6a1ead841af",
  "msgId": "7646739999768969709"
}
```

## Pitfalls

- **SSL certificates**: Corporate deployments (api.bki-okb.ru) use self-signed certs. Use `-k` with curl or configure cert verification.
- **chatId format**: Include `@chat.agent` suffix. The adapter uses full string like `107756@chat.agent`.
- **Token exposure**: The bot token appears in query string. Avoid logging full URLs containing the token.
- **send_message does NOT deliver images**: The Hermes `send_message` tool's `MEDIA:` syntax sends plain text to VK Teams — never use it for image delivery. All media must go through direct API calls (`POST /messages/sendFile` or `GET /messages/sendFile?fileId=...`).
- **Self-signed certs block browser navigation**: When navigating to sites with invalid certs, the browser may fail. Try navigating anyway — sometimes the page still loads despite the error.
- **Home channel**: `VKTEAMS_HOME_CHANNEL` = `107756@chat.agent` — multiple DM sessions share the same bot.
- **replyMsgId must be array per API spec**: The official VK Teams Bot API defines `replyMsgId` as `type: array, items: { type: integer }`. If you're calling the API directly (not via the adapter), pass it as an array: `replyMsgId=[12345]` or `replyMsgId[]=12345`. The built-in adapter may have this bug — verify by checking `/opt/data/plugins/vkteams/adapter.py` line ~84 and ~109.

## Adapter File Upload Override

The base `BasePlatformAdapter.send_document()` and `send_image_file()` fall back to sending file paths as plain text. For VK Teams, override them to actually upload via API. Add to `/opt/data/plugins/vkteams/adapter.py`:

```python
async def send_document(self, chat_id, file_path, caption=None, reply_to=None, metadata=None, **kwargs):
    result = self._send_file(chat_id, file_path=file_path, caption=caption, reply_msg_id=reply_to)
    return SendResult(success=result.get('ok', False), message_id=str(result.get('msgId', '')))

async def send_image_file(self, chat_id, image_path, caption=None, reply_to=None, metadata=None, **kwargs):
    result = self._send_file(chat_id, file_path=image_path, caption=caption, reply_msg_id=reply_to)
    return SendResult(success=result.get('ok', False), message_id=str(result.get('msgId', '')))
```

After modifying the adapter, restart the gateway for changes to take effect.

## API Reference

Full parameter types, response schemas, event types, and spec-fetching commands are documented in `references/api-spec.md`. Use it when debugging API calls or verifying parameter formats against the official OpenAPI spec.

## Session References

- `references/image-send-test-2026-06-04.md` — verified working curl commands for sending images via VK Teams Bot API (multipart/form-data POST /messages/sendFile). Confirms `send_message` with `MEDIA:` prefix does NOT work for VK Teams.