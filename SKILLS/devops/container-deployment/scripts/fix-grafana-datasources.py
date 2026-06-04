#!/usr/bin/env python3
"""Fix datasource bindings on all panels of a Grafana dashboard."""
import json, urllib.request, sys

GRAFANA = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3000"
AUTH_USER = sys.argv[2] if len(sys.argv) > 2 else "admin"
AUTH_PASS = sys.argv[3] if len(sys.argv) > 3 else "grafana123"
DATASOURCE_UID = sys.argv[4] if len(sys.argv) > 4 else None

BASIC_TOKEN = urllib.request.base64.b64encode(f'{AUTH_USER}:{AUTH_PASS}'.encode()).decode()

def api_get(path):
    req = urllib.request.Request(f"{GRAFANA}{path}")
    req.add_header("Authorization", f"Basic {BASIC_TOKEN}")
    return json.loads(urllib.request.urlopen(req).read())

def api_post(path, data):
    body = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(f"{GRAFANA}{path}", data=body, method="POST")
    req.add_header("Authorization", f"Basic {BASIC_TOKEN}")
    req.add_header("Content-Type", "application/json")
    return json.loads(urllib.request.urlopen(req).read())

# Get datasources to find UID if not provided
if not DATASOURCE_UID:
    ds_list = api_get("/api/datasources")
    for ds in ds_list:
        if ds["type"] == "prometheus":
            DATASOURCE_UID = ds["uid"]
            print(f"Using Prometheus datasource: {ds['name']} (UID: {DATASOURCE_UID})")
            break

if not DATASOURCE_UID:
    print("ERROR: Could not find a Prometheus datasource. Pass UID as arg 4.")
    sys.exit(1)

# Find dashboard by query
dashboards = api_get("/api/search?query=Server+Monitoring")
if not dashboards:
    print("ERROR: Dashboard 'Server Monitoring' not found.")
    sys.exit(1)

uid = dashboards[0]["uid"]
db = api_get(f"/api/dashboards/uid/{uid}")['dashboard']

fixed = 0
for panel in db["panels"]:
    old_ds = panel.get("datasource")
    panel["datasource"] = {"uid": DATASOURCE_UID, "type": "prometheus"}
    for target in panel.get("targets", []):
        target["datasource"] = {"uid": DATASOURCE_UID, "type": "prometheus"}
    if old_ds != panel["datasource"]:
        fixed += 1
    print(f"  Panel '{panel['title']}' (id={panel['id']}): {old_ds} -> {DATASOURCE_UID}")

result = api_post("/api/dashboards/db", {"dashboard": db, "overwrite": True})
print(f"\nSaved: {result.get('message', result)}")
print(f"Fixed {fixed} panels")
