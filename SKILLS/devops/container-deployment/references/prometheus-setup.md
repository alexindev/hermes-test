# Prometheus Monitoring Stack Setup

## Session Context
Created June 3, 2026 on hermes-demo (158.160.4.7) — Debian 11, Docker 29.5.2.

## Architecture
```
┌─────────────┐     scrape      ┌──────────────┐
│ Node Exporter│ ──────────────► │ Prometheus   │
│ :9100        │                 │ :9090        │
│ (host)       │                 │              │
└─────────────┘                 └──────┬───────┘
                                       │ API queries
                                       ▼
                               ┌──────────────┐
                               │ Grafana      │
                               │ :3000        │
                               └──────────────┘
```

## Key Files
- `~/monitoring/docker-compose.yml` — service definitions
- `~/monitoring/prometheus/prometheus.yml` — scrape config
- Grafana admin password: `grafana123`

## Datasource UIDs (from this session)
- Prometheus: `afo1076a7n3eoa`
- Node Exporter: `efo1076czj18gf`

## Dashboard UID
- Server Monitoring: `d815549a-f6bd-498c-99d7-32db50cc1f35`

## Common Issues

### Node Exporter not scraping
Symptom: Prometheus target shows `connection refused` for localhost:9100
Root cause: Node Exporter runs with `network_mode: host`, so it's on the host network, not inside Docker. Prometheus container's `localhost` ≠ host's localhost.
Fix: Use Docker gateway IP (see `container-deployment` skill).

### Grafana panels show "No data"
Symptom: Panels render but no metrics appear
Root cause: Dashboard created via API has `datasource: NONE` on all panels
Fix: Explicitly set datasource UID on each panel and each target (see `container-deployment` skill).

### host.docker.internal not resolving
Symptom: `wget: bad address 'host.docker.internal:9100'`
Root cause: Linux Docker doesn't support `host.docker.internal` natively
Fix: Use gateway IP from `docker network inspect`.
