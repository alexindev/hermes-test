# Open WebUI Release Tracking

## 0.9.6 (latest)

**Key changes from 0.9.5:**
- ⚠️ **Database migrations included** — backup DB before upgrading
- WebSocket reconnect status feedback (warns on drop, confirms reconnect)
- Pinned notes in sidebar
- New companion tool `oikb` — smart directory sync for knowledge bases (local dir, GitHub, S3, Confluence, 40+ sources)
- Model-attached skills injected into system prompt instead of...

**Known issues:**
- [Issue #25591](https://github.com/open-webui/open-webui/issues/25591) — chats may stop generating midway on long context (100k+)

**Docker images:**
- `ghcr.io/open-webui/open-webui:v0.9.6`
- `ghcr.io/open-webui/open-webui:v0.9.6-cuda`
- `ghcr.io/open-webui/open-webui:v0.9.6-ollama`

**Previous:** IODD-491 (update to 0.9.5, completed 2026-05-29)
**Current:** IODD-502 (update to 0.9.6, created 2026-06-03)

## Upgrade Procedure (from IODD-502 breakdown)

1. **Backup** — DB dump + config + volumes
2. **Update image** — change docker-compose `v0.9.5` → `v0.9.6`
3. **Run migrations** — automatic on startup, check logs
4. **Validate** — test features, rollback plan ready

## Resources

- [GitHub Releases](https://github.com/open-webui/open-webui/releases)
- [CHANGELOG.md](https://github.com/open-webui/open-webui/blob/main/CHANGELOG.md)
- [Docs — Updating](https://docs.openwebui.com/getting-started/updating/)