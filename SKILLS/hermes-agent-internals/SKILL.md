---
name: hermes-agent-internals
description: Understanding Hermes Agent internals — gateway architecture, platform registration, plugin system, config loading, and adapter lifecycle. Use when debugging why a platform isn't connecting, tracing message flow, or understanding how the gateway discovers and instantiates adapters.
---

# Hermes Agent Internals

Understanding how Hermes Agent gateway works under the hood. Covers platform registration, plugin mechanics, config loading, and adapter lifecycle.

## Gateway Platform Registration System

### Two-tier adapter lookup

When the gateway starts, it iterates over `config.yaml` platforms (NOT `Platform` enum). For each enabled platform, it calls `_create_adapter()` in `gateway/run.py`:

1. **Plugin registry check FIRST** — calls `platform_registry.is_registered(platform.value)`. If registered, uses `platform_registry.create_adapter()` which checks `check_fn()`, `validate_config()`, then calls `adapter_factory(config)`.
2. **Built-in fallback** — only if plugin registry returns nothing, falls through to if/elif chain for hardcoded platforms (telegram, discord, slack, etc.).

Key: Plugin platforms do NOT need to be in the `Platform` enum. The gateway iterates over config keys as strings, and the registry accepts any name.

### Where to look

| Component | File | Purpose |
|-----------|------|---------|
| Platform registry | `gateway/platform_registry.py` | `PlatformEntry` dataclass + `PlatformRegistry` singleton |
| Plugin registration | `hermes_cli/plugins.py` line ~613 | `PluginContext.register_platform()` method |
| Adapter creation | `gateway/run.py` line ~5256 | `_create_adapter()` — the two-tier lookup |
| Startup loop | `gateway/run.py` line ~3554 | Iterates `self.config.platforms.items()` |
| Platform enum | `gateway/config.py` | `Platform` enum — only for built-in adapters |

### PlatformEntry fields (the important ones)

- `name` — string used in config.yaml
- `label` — human-readable display name
- `adapter_factory` — callable(config) → adapter instance
- `check_fn` — returns True when deps are available
- `validate_config` — optional, validates config before instantiation
- `allowed_users_env` / `allow_all_env` — auth integration
- `max_message_length` — smart-chunking limit
- `pii_safe` — session redaction
- `cron_deliver_env_var` — cron notification home channel
- `standalone_sender_fn` — out-of-process message sending
- `apply_yaml_config_fn` — YAML→env config bridge

## Common Debugging Patterns

### Platform not connecting?

1. Check `config.yaml` — is the platform enabled?
2. Check `platform_registry.is_registered(name)` — was it registered by a plugin?
3. Check `check_fn()` — are dependencies installed?
4. Check `validate_config()` — is the config valid?
5. Check `adapter_factory()` — does it raise?
6. Check `connect()` — connection failure vs. instantiation failure

### No adapter available warning

The gateway distinguishes between:
- Platform value not in `Platform.__members__` → "is the plugin installed?"
- Platform value IS in enum but factory returned None → missing deps or bad config

### Group/chat filtering

Each platform implements its own group filtering:
- Telegram: `_telegram_allowed_chats()` — reads `allowed_chats` from config
- DingTalk: `_dingtalk_allowed_chats()` — same pattern
- WhatsApp: `_is_group_allowed()` — reads from config
- Generic: `group_chat_allowlist` env var checked in `run.py` ~line 5595

If a platform has no group filtering, it processes ALL messages from connected chats.

## Config Loading Flow

1. `load_gateway_config()` reads `~/.hermes/config.yaml`
2. Shared keys (token, model, etc.) extracted first
3. Per-platform YAML configs parsed
4. `apply_yaml_config_fn` called for plugins that define it
5. Env var overrides applied (`_apply_env_overrides`)
6. `PlatformConfig` instances created with merged config

## Key Files Reference

```
gateway/
  run.py              — GatewayRunner, _create_adapter(), startup loop
  config.py           — Platform enum, PlatformConfig, load_gateway_config()
  platform_registry.py — PlatformEntry, PlatformRegistry, platform_registry singleton

hermes_cli/
  plugins.py          — PluginContext.register_platform(), PluginManager

gateway/platforms/    — Built-in adapter implementations
```

## Pitfalls

- **Don't assume platforms come from `Platform` enum** — plugin platforms register by string name only
- **`_create_adapter` checks registry BEFORE if/elif** — plugin adapters take priority over built-ins with the same name
- **Group filtering is per-platform** — there is no universal "which groups to monitor" setting; each adapter decides
- **Empty proxy files = no adapter** — if `/opt/data/vk_teams_proxy.py` is empty or missing, there is no VK Teams support regardless of config
- **Config iteration uses string keys** — `self.config.platforms.items()` yields `(Platform, PlatformConfig)` tuples, but the key can be a non-enum platform if a plugin registered it
