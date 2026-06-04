# VK Teams Image Send Test — 2026-06-04

## Context
Tested sending a browser screenshot (bki-okb.ru) via VK Teams Bot API after confirming that `send_message` with `MEDIA:` prefix does NOT work for VK Teams.

## Test: Screenshot of bki-okb.ru

### Steps
1. Captured screenshot via `browser_vision` → saved to `/opt/data/cache/screenshots/browser_screenshot_876b8c20b374469a9fc1176907d0b5d2.png`
2. Sent via direct API call:

```bash
curl -s -X POST \
  "https://api.bki-okb.ru/bot/v1/messages/sendFile" \
  -F "token=001.0878497284.4267979501:1000000100" \
  -F "chatId=10756@chat.agent" \
  -F "file=@/opt/data/cache/screenshots/browser_screenshot_876b8c20b374469a9fc1176907d0b5d2.png" \
  -F "caption=Скриншот главной страницы bki-okb.ru"
```

### Result
```json
{"fileId": "095ZZ000TtlH6wZbnjgE9x6a214bc11af", "msgId": "7647476934552585664", "ok": true}
```

✅ Image successfully delivered to VK Teams chat.

### Key Takeaway
- Direct `POST /messages/sendFile` with `multipart/form-data` works reliably for sending images to VK Teams.
- The adapter's `_send_file` method wraps this same endpoint — use it programmatically.
- `send_message` tool with `MEDIA:` prefix is NOT supported by VK Teams platform.
