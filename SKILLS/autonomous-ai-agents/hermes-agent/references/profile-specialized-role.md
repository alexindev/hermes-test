# Настройка изолированного профиля для специализированной роли

Полный рабочий процесс создания профиля Hermes Agent для узкоспециализированной роли (DBA, DevOps, аналитик и т.д.) с изолированными инструментами, моделью и доступом к внешним сервисам.

## Когда использовать

- Пользователь хочет изолированную среду для конкретной роли (только БД, только мониторинг, только разработка)
- Нужен профиль с ограниченным набором toolsets (не все 30+)
- Требуется отдельная модель / MCP-сервер / personality для роли
- Нужно отделить историю сессий и память от основного профиля

## Шаг 1: Подготовка структуры директорий

```bash
PROFILE=/opt/data/profiles/<name>
mkdir -p $PROFILE/{cron,home,logs,memories,plans,sessions,skins,workspace}
```

Все поддиректории обязательны — Hermes ожидает их наличие при загрузке профиля.

## Шаг 2: Создание .env профиля

```bash
cat > $PROFILE/.env << 'EOF'
DATABASE_URL=postgresql://user:pass@host:port/dbname
SEARXNG_URL=http://localhost:8888
# ... другие переменные, нужные ТОЛЬКО для этой роли
EOF
```

**Важно:** Не копируйте `.env` из основного профиля без фильтрации. Уберите токены мессенджеров, браузерные настройки, API-ключи, не нужные для роли.

## Шаг 3: Симлинки на skills

Профиль не дублирует skills — создаёт симлинки на нужные:

```bash
cd $PROFILE/skills
ln -s /opt/data/skills/data-science .
ln -s /opt/data/skills/mcp .
ln -s /opt/data/skills/hermes-agent-internals .
```

Глобальные skills подгружаются автоматически при наличии симлинков. Не нужно копировать — только ссылки.

## Шаг 4: Создание SOUL.md

Файл `SOUL.md` задаёт персонализацию внутри профиля (стиль общения, контекст предметной области, правила работы):

```markdown
# SOUL.md — Role: <ROLE_NAME>

## Роль
Ты — <ROLE_DESCRIPTION>. Работай на русском языке, технически точно, лаконично.

## Предметная область
<Описание БД, систем, инструментов — конкретные таблицы, API, сервисы>

## Правила работы
- <правило 1>
- <правило 2>
```

Пример для DBA:
```markdown
## Предметная область
БД Bigdata: 11 таблиц (sellers, stores, products, categories, orders, orders_products, reviews, seller_ratings, users, baskets, wishlists), UUID FKs.

## Правила работы
- Показывать SQL-запрос вместе с результатом
- НИКОГДА не выполнять DELETE, UPDATE, INSERT — только SELECT
- Работать только через MCP postgres-mcp в режиме READ-ONLY
```

## Шаг 5: Конфигурация config.yaml

Ключевые секции для специализированного профиля:

```yaml
model:
  default: "provider/model-name"
  provider: custom
  base_url: "http://host:port/v1"

toolsets:
  - terminal
  - file
  - skills

disabled_toolsets:
  - web
  - browser
  - vision
  - image_gen
  - video
  - tts
  - spotify
  - homeassistant
  - discord
  - feishu_doc
  - feishu_drive
  - yuanbao
  - x_search
  - delegation
  - cronjob
  - kanban

personalities:
  db_admin:
    system_prompt: |
      Ты — опытный DBA. Отвечай на русском, технически точно, лаконично.
      #include SOUL.md

mcp_servers:
  postgres:
    command: ["uvx", "postgres-mcp", "--access-mode=restricted"]
    env:
      DATABASE_URI: "postgresql://postgres:@host.docker.internal:6432/bigdata"
```

## Шаг 6: Переключение в gateway режиме

В gateway профиле НЕЛЬЗЯ переключить mid-session. Нужно перезапустить gateway:

```bash
# Проверить текущий процесс
ps aux | grep "hermes gateway" | grep -v grep

# Убить
kill <PID>

# Перезапустить с новым профилем
cd /opt/hermes && HERMES_HOME=/opt/data/home/.hermes .venv/bin/python3 /opt/hermes/.venv/bin/hermes gateway run -p <name>
```

VK Teams отключится на ~10 секунд.

## Checklist готовности профиля

- [ ] Все директории созданы (cron, home, logs, memories, plans, sessions, skins, workspace)
- [ ] `.env` содержит только нужные для роли переменные
- [ ] Симлинки на skills ведут на правильные пути
- [ ] `SOUL.md` описывает предметную область и правила
- [ ] `config.yaml`: модель, toolsets, disabled_toolsets, personalities, mcp_servers
- [ ] `display.personality` указывает существующую personality
- [ ] Профиль виден в `~/.hermes/profiles/<name>/`

## Частые ошибки

| Ошибка | Причина | Решение |
|--------|---------|---------|
| Профиль не грузится | Пропущена директория | Создать все 8 поддиректорий |
| Skills не доступны | Нет симлинков | Создать `ln -s` на нужные skills |
| MCP не подключается | Неправильный DATABASE_URI | Проверить хост (`host.docker.internal` vs IP) и порт |
| Personality не применяется | Имя в `display.personality` не совпадает с ключом в `personalities:` | Сопоставить имена |
| Gateway не переключается | Попытка `/profile` mid-session | Перезапустить gateway с `-p <name>` |
| Профиль не виден в `hermes profile list` | Лежит в `~/.hermes/profiles/` вместо `$HERMES_HOME/profiles/` | Переместить в правильное место (см. ниже «Профиль спрятался») |
| В изолированном профиле мусор от default | Клонирован через `--clone default` | Не клонировать, а создать минимальный конфиг вручную (см. ниже «Клонирование = мусор») |

### Профиль спрятался

Hermes ищет профили в `$HERMES_HOME/profiles/`. В Docker-развёртках это обычно `/opt/data/profiles/`. Если профиль создан в `~/.hermes/profiles/` (стандартный путь для локальных установок), он **не появится** в `hermes profile list`:

```bash
# Найти потерянный профиль
find ~/.hermes/profiles /opt/data/profiles -maxdepth 2 -name "config.yaml" 2>/dev/null

# Переместить в правильное место
cp -r ~/.hermes/profiles/db /opt/data/profiles/db
```

### Клонирование = мусор

`hermes profile create --clone default` копирует **весь** config из default: MCP postgres, VK Teams, Telegram, Discord, Slack, TTS, браузер, kanban, cron… Для изолированного профиля это 95% ненужного.

**Правильный подход:** создать пустой профиль и написать конфиг вручную:

```bash
# 1. Удалить неудачный клон (если уже создал)
rm -rf /opt/data/profiles/code

# 2. Создать чистый профиль без навыков
hermes profile create --no-skills code

# 3. Написать минимальный config.yaml вручную
#    Только model + toolsets, которые нужны для роли
```

Минимальный config для профиля программирования (~600 байт):
```yaml
_config_version: 23
agent:
  max_turns: 90
  tool_use_enforcement: auto
model:
  default: palmfuture/Qwen3.6-35B-A3B-GPTQ-Int4
  provider: custom
  base_url: http://khd-llm-app01.ipa.dev.ucb.local:11434/v1
  api_mode: chat_completions
toolsets:
  - terminal
  - file
  - search
  - web
  - delegation
  - skills
  - todo
  - session_search
  - memory
memory:
  memory_enabled: true
  user_profile_enabled: true
```

## Сравнение профилей

| Setting | Меняется при смене профиля | Требует рестарта? |
|---------|---------------------------|-------------------|
| model / provider | ✅ | Да |
| personality | ✅ | Да |
| disabled_toolsets | ✅ | Да |
| mcp_servers | ✅ | Да |
| Память | ✅ Изолирована | N/A |
| Сессии | ✅ Изолированы | N/A |

Для изменения tools/personality mid-session без рестарта: `/personality <name>` или `/toolsets` — но это НЕ меняет MCP и модель.
