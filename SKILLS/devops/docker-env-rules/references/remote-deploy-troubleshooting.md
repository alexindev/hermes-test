# Remote Docker Deployment Troubleshooting

## Session: June 3, 2026 — hermes-demo (158.160.4.7)

### Issue: Docker permission denied
**Symptom:** `unable to get image 'prom/node-exporter:latest': permission denied while trying to connect to the docker API at unix:///var/run/docker.sock`

**Fix:** Add user to docker group:
```bash
sudo usermod -aG docker hermes
newgrp docker
```

### Issue: Compose version warning
**Symptom:** `the attribute 'version' is obsolete, it will be ignored, please remove it to avoid potential confusion`

**Fix:** Remove `version: "3.8"` from top of docker-compose.yml. Modern Docker Compose ignores it.

### Issue: Image pull timeout
**Symptom:** Large images (grafana ~200MB+) take a long time to pull, command appears stuck.

**Fix:** Use background execution with `notify_on_complete=true` or just wait. Check progress with `docker images`.

### Issue: Node Exporter not collecting metrics
**Symptom:** Prometheus scrapes but node_exporter metrics are empty/missing.

**Fix:** Node Exporter needs host namespace access:
```yaml
node-exporter:
  network_mode: host
  pid: host
  volumes:
    - /proc:/host/proc:ro
    - /sys:/host/sys:ro
    - /:/rootfs:ro
  command:
    - "--path.procfs=/host/proc"
    - "--path.sysfs=/host/sys"
```

### File transfer pattern
Use SCP to push compose files and configs:
```bash
scp -i <key> docker-compose.yml prometheus.yml hermes@<ip>:~/monitoring/
```

Then SSH to run:
```bash
ssh -i <key> hermes@<ip> 'cd ~/monitoring && docker compose up -d'
```
