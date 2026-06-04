# VK Teams Bot API — Official Spec Notes

Source: `https://teams.vk.com/botapi/` (OpenAPI 3.0.0, fetched via `/botapi/api.yaml`)

## Key Parameter Types

### replyMsgId
- **Type**: `array of integer`
- **Required**: No
- **In**: query
- **Note**: The adapter may pass this as a single value — if reply-to fails, check it's sent as array.

### fileId
- **Type**: `string`
- **Required**: Yes (for GET /messages/sendFile)
- **In**: query
- **Description**: Previously uploaded file ID for cheap resend.

### pollTime
- **Type**: `integer`
- **Required**: Yes
- **In**: query
- **Default in adapter**: 30 seconds (env var `VKTEAMS_POLL_TIME`)

### lastEventId
- **Type**: `integer`
- **Required**: Yes
- **In**: query
- **Starts at**: 0

### caption
- **Type**: `string`
- **Required**: No
- **In**: query
- **Used by**: Both POST and GET /messages/sendFile

## Response Schemas

### Text send (msgOk)
```json
{ "ok": true, "msgId": "57883346846815032" }
```

### File send (msgLoadFileOk)
```json
{ "ok": true, "msgId": "57883346846815032", "fileId": "0dC76vcKS3XZOtG5DVs9y15d1daefa1ae" }
```

## Event Types (from schemas.json)

| type | Description |
|------|-------------|
| `newMessage` | New message in chat |
| `editedMessage` | Message was edited |
| `deletedMessage` | Message was deleted |
| `pinnedMessage` | Message was pinned |
| `unpinnedMessage` | Message was unpinned |
| `newChatMembers` | Users added to chat |
| `leftChatMembers` | Users removed/left chat |
| `callbackQuery` | Inline button callback |

## Adapter Source Location

- **Running copy**: `/opt/data/plugins/vkteams/adapter.py` (mounted into Docker)
- **Repo backup**: `hermes-test/vkteams/adapter.py` (exact copy, pushed via PR #18)
- **Plugin manifest**: `hermes-test/vkteams/plugin.yaml`

## How to Fetch the Spec

```bash
curl -sk 'https://teams.vk.com/botapi/api.yaml' -o api.yaml
curl -sk 'https://teams.vk.com/botapi/events/get.json' -o events_get.json
curl -sk 'https://teams.vk.com/botapi/messages/sendFile.json' -o sendfile.json
curl -sk 'https://teams.vk.com/botapi/messages/sendText.json' -o sendtext.json
curl -sk 'https://teams.vk.com/botapi/params.json' -o params.json
curl -sk 'https://teams.vk.com/botapi/schemas.json' -o schemas.json
curl -sk 'https://teams.vk.com/botapi/responses.json' -o responses.json
```
