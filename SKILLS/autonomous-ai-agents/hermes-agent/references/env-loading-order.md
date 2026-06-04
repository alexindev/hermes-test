# .env Loading Order in Hermes Agent

## Lifecycle

1. **main.py line 210-212** — `load_hermes_dotenv(project_env=PROJECT_ROOT / ".env")`
   - This is the FIRST thing that happens at import time, before any agent, gateway, or plugin code runs.
   - Both user env and project env are loaded here.

2. **Bridge config.yaml → env vars** — redact_secrets, IPv4 preference (lines 219-256)
   - Config values bridge into os.environ as fallback.

3. **Logging setup** — hermes_logging.setup_logging()

4. **Agent/gateway/plugin imports** — all subsequent modules see os.environ already populated.

## File Resolution

```python
home_path = Path(hermes_home or os.getenv("HERMES_HOME", Path.home() / ".hermes"))
user_env = home_path / ".env"           # ~/.hermes/.env by default
project_env_path = PROJECT_ROOT / ".env" # dev fallback
```

`HERMES_HOME` overrides the default: `~/.hermes/.env` → `$HERMES_HOME/.env`.

## Precedence Rules (from env_loader.py)

| Condition | Behavior |
|-----------|----------|
| User env (`~/.hermes/.env`) exists | Override shell exports; project env only fills MISSING values |
| No user env | Project env overrides shell exports |

Both files are sanitized before parsing (corrupted lines split, non-ASCII stripped from credential vars).

## Key Insight

`.env` loads BEFORE plugins. When plugins read `os.environ.get("VKTEAMS_BOT_TOKEN")` or similar, those values are already set. The load order is:

```
.env → config.yaml bridge → logging → network → agent → gateway → plugins
```

Plugins never need to call `load_dotenv()` themselves — the values are already in `os.environ`.
