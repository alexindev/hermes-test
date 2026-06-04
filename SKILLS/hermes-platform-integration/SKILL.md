---
name: hermes-platform-integration
description: "Deploy Hermes Agent platform adapters (VK Teams, Telegram, Discord) to new instances."
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [hermes, platform, adapter, integration, deployment, vkteams]
    related_skills: [docker-compose-deployment, container-deployment]
---

# Hermes Platform Adapter Integration

Deploy a Hermes Agent platform adapter to a new Hermes instance. Covers VK Teams as primary reference.

## What to copy

### 1. Plugin files (`/opt/data/plugins/<name>/`)

Three files minimum:

| File | Purpose |
|------|---------|
| `adapter.py` | Main adapter logic (send_message, send_file, reply-to, etc.) |
| `plugin.yaml` | Metadata: required env vars, version, description |
| `__init__.py` | Entry point: `from .adapter import register` |

Skip `__pycache__/` — regenerated on import.

### 2. Gateway config (`config.yaml`)

Two sections:

```yaml
gateway:
  enabled:
    - <platform_name>   # add to this list

<platform_name>:
  require_mention: true   # or other platform-specific settings
```

### 3. Environment variables (`.env`)

Extract all `<PLATFORM>_*` vars from source `.env`. Two categories:

- **Required**: token, base URL, allowed chats (check `plugin.yaml` `requires_env`)
- **Optional**: home channel, bot mention string, chat→skill mapping (`VKTEAMS_CHAT_*_SKILL`)

### 4. Python dependencies

Check `import` statements in `adapter.py`. Install missing packages:
```bash
/opt/data/hermes-tools/.venv/bin/pip install <package>
```

## Pitfalls

### ❌ Never bypass the adapter with curl/wget

If the adapter has built-in methods (e.g., `_send_file()`, `send_document()`), use them directly — don't fall back to raw HTTP calls. The adapter handles auth, formatting, and API spec compliance.

**Wrong pattern**: seeing `send_message` fail → immediately using curl to the same endpoint.
**Right pattern**: check `adapter.py` for existing methods first; only use direct API if no method exists.

### Always check `plugin.yaml` for required env vars

The `requires_env` section lists mandatory variables. Missing one will cause the adapter to fail silently or crash on startup.

### Verify `replyMsgId` format matches API spec

Some adapters need fixes for API spec compliance (e.g., VK Teams requires `replyMsgId` as array `[msg_id]`, not scalar). Check the official API spec before deploying.

## Verification

After deployment:
1. Confirm `pip install` covers all imports in `adapter.py`
2. Verify `.env` has all required platform vars
3. Confirm `config.yaml` has platform in `gateway.enabled` list
4. Restart gateway and test with a simple message
5. Test file sending via adapter's built-in method (not curl)

## References

- See `references/vkteams-integration.md` for VK Teams-specific details and env var patterns.
