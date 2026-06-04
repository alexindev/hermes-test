---
name: netbox-lookup
title: NetBox Infrastructure Lookup Patterns
description: Multi-step patterns for finding VLANs, IPs, and connectivity in NetBox from hostnames or IP addresses.
tags:
  - netbox
  - vlan
  - ipam
  - prefix
  - virtual-machine
  - ssh
---

# NetBox Infrastructure Lookup

## Finding VLAN for a hostname/IP

When you need to find which VLAN a device uses in NetBox:

1. **Search by partial hostname** — use `netbox_search_objects` with a truncated name (full FQDN often fails; strip `.ipa.dev.ucb.local`, `.ucb.infra`, etc.)
   ```
   netbox_search_objects('naumen-app01')  # try partial name first
   ```

2. **If not found as device**, check `virtualization.virtualmachine` — the search returns both types. Look for `custom_fields.vcsa_vm_guest_hostname` matching the FQDN.

3. **Extract primary IP** from the VM object → `primary_ip4.address` (e.g., `10.8.123.68/24`).

4. **Find the prefix** using exact match on the /24 network:
   ```
   netbox_get_objects(object_type='ipam.prefix', filters={'prefix': '10.8.123.0/24'}, limit=5)
   ```
   Use the network address (strip the host octet from the IP).

5. **Get VLAN** from the prefix result → `vlan.name`, `vlan.vid`.

### Example workflow
```
# 1. Search by partial name
netbox_search_objects('kvk-naumen-app01') → finds VM id=6022

# 2. Extract IP from VM → 10.8.123.68/24

# 3. Query prefix exactly
netbox_get_objects('ipam.prefix', {'prefix': '10.8.123.0/24'}) → vlan: k.pvt.net.polygon (VID 2111)
```

## Pitfalls

1. **Full FQDN search fails** — `netbox_search_objects('kvk-naumen-app01.ipa.dev.ucb.local')` returns empty. Strip the domain suffix first.
2. **Prefix search needs exact CIDR** — use `{"prefix": "10.8.123.0/24"}` (exact match), NOT range operators.
3. **Overlapping prefixes** — searching with `prefix__ie` (is enclosed by) returns hundreds of results. Use exact `prefix` match instead.
4. **VM vs Device** — modern infrastructure uses `virtualization.virtualmachine` more than `dcim.device`. Always check both.
5. **SSH key location** — in Hermes Docker container, SSH keys are at `/tmp/hermes-ssh/id_ed25519`, NOT in `~/.ssh/`.

## Quick SSH Connectivity Check

After finding the target in NetBox, verify actual connectivity:
```bash
ssh -i /tmp/hermes-ssh/id_ed25519 -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l <user> <host> "hostname; uptime"
```

## Integration Test Pattern

To verify all connected systems work in one pass, run these checks in parallel:
- PostgreSQL: `mcp_postgres_execute_sql("SELECT current_user, current_database()")`
- Confluence: `mcp_atlassian_confluence_search(query="space=IODD", limit=1)`
- Jira: `mcp_atlassian_jira_search(jql="project=IODD ORDER BY updated DESC", limit=1)`
- NetBox: `mcp_netbox_netbox_get_objects('dcim.site', {'slug': '<site_slug>'}, limit=1)`
- GitHub: `terminal("gh auth status")`
- SSH: `terminal("ssh -i /tmp/hermes-ssh/id_ed25519 ...")`