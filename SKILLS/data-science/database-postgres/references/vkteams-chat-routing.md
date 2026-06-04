# VK Teams Per-Chat Role Configuration

When running Hermes on VK Teams with multiple group chats, you can assign different roles/personalities to each chat using environment variables.

## Pattern: System Prompt per Chat

Use `VKTEAMS_CHAT_<CHAT_ID>_SYSTEM_PROMPT` to inject a custom system message for messages coming from a specific chat.

### Example

```env
VKTEAMS_CHAT_107756_SYSTEM_PROMPT=You are a helpful general-purpose AI assistant. Help with project management, coordination, and general questions. Be concise but thorough.

VKTEAMS_CHAT_107890_SYSTEM_PROMPT=You are a database specialist assistant. You work with PostgreSQL databases. Help with queries, schema design, optimization, migrations, and data analysis. Always be careful with destructive operations. Use proper SQL syntax and explain your reasoning.

VKTEAMS_CHAT_107896_SYSTEM_PROMPT=You are a software development assistant. Help with coding, debugging, code review, architecture, and development workflows. Write clean, well-commented code. Follow best practices. Use the terminal and file tools to actually implement changes.
```

## Required Supporting Variables

```env
VKTEAMS_ALLOWED_CHATS=107756@chat.agent,107890@chat.agent,107896@chat.agent
VKTEAMS_HOME_CHANNEL=107756@chat.agent
VKTEAMS_ALLOW_ALL_USERS=true
```

## Important Notes

- **No @mention required** — all messages in allowed chats are processed automatically. Do NOT set `VKTEAMS_CHAT_*_REQUIRE_MENTION=true` unless you explicitly want mention-only mode.
- **Skills vs System Prompts** — prefer `VKTEAMS_CHAT_<ID>_SYSTEM_PROMPT` over `VKTEAMS_CHAT_<ID>_SKILL`. Skill names must match actual SKILL.md files in `/opt/data/skills/`, and missing skills silently fail. System prompts are simpler and always take effect.
- Changes take effect on gateway restart (`hermes gateway restart`) or new session (`/reset`).
