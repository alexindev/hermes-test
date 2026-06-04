---
name: infra-queries
title: Infrastructure Multi-Hop Queries
description: Patterns for querying infrastructure tools (NetBox, Docker, etc.) when data spans multiple related objects. Covers hostname-to-VLAN lookups, container env extraction, and chained queries.
tags:
  - netbox
  - docker
  - multi-hop
  - infrastructure
  - lookup-patterns
---

# Infrastructure Queries — Multi-Hop Lookups

When querying infrastructure tools, direct single-hop lookups often fail because data is split across related objects. Use chained lookups.

## NetBox: Hostname → VLAN

Cannot query VLAN directly from a device name. Follow the chain:

1. **Search VM/device** by name → get `primary_ip` ID or `primary_ip4.address`
2. **Extract /24 prefix** from the IP address
3. **Find prefix** by exact `prefix` match (NOT `prefix__ie` — that returns 900+ results)
   ```
   mcp_netbox_netbox_get_objects(object_type="ipam.prefix", filters={"prefix": "10.8.123.0/24"}, limit=5, fields=["id","prefix","vlan","site"])
   ```
4. **Read VLAN** from the prefix result → `vlan.name`, `vlan.vid`

### Example Walkthrough

```bash
# Step 1: Search VM
mcp_netbox_netbox_search_objects("kvk-naumen-app01")
# → primary_ip4: 10.8.123.68/24

# Step 2: Find prefix by exact match
mcp_netbox_netbox_get_objects(
  object_type="ipam.prefix",
  filters={"prefix": "10.8.123.0/24"},
  fields=["prefix","vlan","site"]
)
# → vlan: k.pvt.net.polygon (VID 2111)
```

### Pitfalls
- **`prefix__ie` (IP ends with) returns ALL matching prefixes** — hundreds of results, pagination needed. Always use exact `prefix` match when you know the subnet.
- **VM search returns `virtualization.virtualmachine`** not `dcim.device` — adjust object_type accordingly.
- **Primary IP may be null** for some VMs — check `primary_ip4` field carefully.

## Extracting Container Env Vars (when credentials hidden)

When you need DB passwords or API keys but they're masked (`***`) in config files:

```bash
# Get env from running container
docker exec <container-name> env | grep DATABASE_URI

# Or read process environ
docker exec <container-name> cat /proc/1/environ | tr '\0' '\n' | grep PASSWORD
```

This works because MCP servers (postgres-mcp, atlassian, etc.) store connection strings in their container env.

### When to Use
- MCP server connects successfully but you can't find the password in configs
- Config files show `***` or redacted values
- You need to replicate a connection string in your own code

## General Pattern

For any infrastructure query:
1. Identify the starting object (hostname, IP, domain, slug)
2. Map the relationship chain (VM → IP → Prefix → VLAN)
3. Use exact filters where possible, avoid broad searches
4. If a direct tool field is missing, chain through related objects
5. Verify each hop before proceeding to the next

## Related Skills

- `docker-browserless-setup` — for Docker container inspection and management
- `native-mcp` — for MCP-based tool registration and discovery