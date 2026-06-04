# NetBox MCP Server (netboxlabs/netbox-mcp-server)

## Package info
- GitHub: https://github.com/netboxlabs/netbox-mcp-server
- Docker: `netboxlabs/netbox-mcp-server:latest`
- PyPI: not published (install from source via git clone + uv sync)
- Docs: https://netboxlabs.com/docs/mcp/

## Installation (from GitHub)

```bash
git clone https://github.com/netboxlabs/netbox-mcp-server.git
cd netbox-mcp-server
uv sync
```

## Hermes Agent config (stdio transport)

```yaml
mcp_servers:
  netbox:
    command: uv
    args:
      - --directory
      - /path/to/netbox-mcp-server
      - run
      - netbox-mcp-server
      - --no-verify-ssl       # required if NetBox has self-signed TLS cert
    env:
      NETBOX_URL: "https://netbox-test.ucb.infra/"
      NETBOX_TOKEN: "<your-read-only-api-token>"
```

## Verification

```bash
hermes mcp test netbox
# Expected output: ✓ Connected (with tool count)
# ✓ Tools discovered: 4
```

Then in-session: run `/reload-mcp` (or `/reset`) to register the tools.

## Tools exposed

| Tool | Description |
|------|-------------|
| `netbox_get_objects` | Retrieves objects by type (devices, sites, prefixes, IPs, VLANs, interfaces, etc.) with filters and optional `fields` parameter for token-efficient queries |
| `netbox_get_object_by_id` | Detailed info about a specific object by its ID |
| `netbox_get_changelogs` | Change history / audit trail records |
| `netbox_search_objects` | Global search across all NetBox object types |

### Field filtering (token optimization)

Both `get_objects` and `get_object_by_id` accept an optional `fields` parameter:

```python
# Without fields: ~5000 tokens for 50 devices
get_objects("devices", {"site": "dc-1"})

# With fields: ~500 tokens (90% reduction)
get_objects("devices", {"site": "dc-1"}, fields=["id", "name", "status", "site"])
```

Common field patterns:
- **Devices:** `["id", "name", "status", "device_type", "site", "primary_ip4"]`
- **IP Addresses:** `["id", "address", "status", "dns_name", "description"]`
- **Interfaces:** `["id", "name", "type", "enabled", "device"]`
- **Sites:** `["id", "name", "status", "region", "description"]`

## Docker usage

```bash
docker run --rm \
  -e NETBOX_URL=https://netbox-test.ucb.infra/ \
  -e NETBOX_TOKEN=<token> \
  -e TRANSPORT=http \
  -e HOST=0.0.0.0 \
  -e PORT=8000 \
  -p 8000:8000 \
  netboxlabs/netbox-mcp-server:latest
```

Then connect via SSE transport in config.yaml:
```yaml
mcp_servers:
  netbox:
    url: "http://host.docker.internal:8000/mcp"
```

## Object types supported

All core NetBox modules: DCIM (devices, sites, racks, interfaces, cables), IPAM (IP addresses, prefixes, VLANs, VRFs, ASNs), Circuits, Virtualization, Tenancy, VPN, Wireless, Extras (config contexts, tags, webhooks).

Plugin object types can be auto-discovered with `ENABLE_PLUGIN_DISCOVERY=true` (requires NetBox 4.2+).

## Pitfalls

- **Read-only by design.** The server exposes no create/update/delete tools — this is intentional and safe.
- **Self-signed certificates.** NetBox Community instances commonly use self-signed TLS. Pass `--no-verify-ssl` or set `VERIFY_SSL=false` in env.
- **Requires a read-only API token** created in NetBox under Admin → Users → API Tokens.
- **Tools don't appear immediately** after adding the config. Run `/reload-mcp` in-session or start a fresh session with `/reset`.
- **`netbox_get_*` tool prefix** — server name in config.yaml determines the prefix. With `netbox`, tools are `mcp_netbox_get_objects`, etc.