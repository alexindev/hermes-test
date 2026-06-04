# Grafana Dashboard Automation via API

## Pattern: create datasources and dashboards programmatically using Python + requests

### Authentication
```python
import requests
session = requests.Session()
session.auth = ("admin", "grafana123")
session.headers.update({"Content-Type": "application/json"})
```

### Add Datasource
```python
ds = {
    "name": "Prometheus",
    "type": "prometheus",
    "access": "proxy",
    "url": "http://localhost:9090",
    "jsonData": {"httpMethod": "POST", "timeInterval": "15s"}
}
session.post(f"{GRAFANA_URL}/api/datasources", json=ds)
```

### Create Dashboard
Dashboard is a nested JSON object with `dashboard.panels[]` array. Each panel has:
- `id`: unique integer
- `type`: stat, gauge, timeseries, table, graph, etc.
- `title`: display name
- `gridPos`: {"h": height, "w": width, "x": x, "y": y} — 24-column grid
- `targets`: list of Prometheus query objects with `expr` and `legendFormat`
- `fieldConfig`: thresholds, units, color mappings

### Panel types reference
| Type | Use case | Key config |
|------|----------|-----------|
| `stat` | Single metric value | fieldConfig.thresholds |
| `gauge` | Percentage/meter | fieldConfig.max |
| `timeseries` | Time-series chart | targets[].expr |
| `table` | Raw data rows | format: "table", instant: true |

### Common Prometheus queries for Node Exporter
- CPU usage: `100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)`
- Memory usage: `(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100`
- Disk read: `rate(node_disk_read_bytes_total[5m])`
- Disk write: `rate(node_disk_written_bytes_total[5m])`
- Network in: `rate(node_network_receive_bytes_total{device!~"lo"}[5m])`
- Network out: `rate(node_network_transmit_bytes_total{device!~"lo"}[5m])`

### Session example (June 3, 2026)
Deployed monitoring stack on hermes-demo (158.160.4.7):
- Grafana on port 3000, Prometheus on 9090, Node Exporter on 9100
- Created dashboard "Server Monitoring" with 5 panels via API
- All services running via docker-compose up -d
