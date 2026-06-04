# NetBox Multi-Step Lookup Patterns

Common infrastructure query patterns for NetBox via MCP tools.

## Pattern 1: VM → VLAN (full chain)

When you need to find which VLAN a VM uses, follow this chain:

1. **Search VM** by name → get `primary_ip4.id` and IP address
2. **Extract subnet** from IP (e.g. `10.8.123.68/24` → `10.8.123.0/24`)
3. **Find prefix** matching that subnet → read `vlan` field

```
Example: kvd-naumen-app01.ipa.dev.ucb.local
  ├─ VM search → id=6022, primary_ip4=10.8.123.68/24
  ├─ Prefix lookup → 10.8.123.0/24
  └─ VLAN → k.pvt.net.polygon (VID 2111)
```

## Pattern 2: IP Address → VLAN (reverse)

Given an IP, find its VLAN without knowing the VM:

1. Search IP by address → get associated prefix
2. Get prefix details → read `vlan` field

```python
# Step 1: find prefix containing this IP
get_objects("ipam.prefix", {"prefix": "10.8.123.0/24"}, fields=["id", "prefix", "vlan"])
# Step 2: vlan.name, vlan.vid are on the prefix object
```

## Pattern 3: Site Inventory Summary

Quick overview of all sites:

```python
get_objects("dcim.site", {}, fields=["id", "name", "status", "slug"], limit=50)
```

## Pattern 4: Device Interface Details

Get interfaces for a specific device:

```python
get_objects("dcim.interface", {"device": "device-name"}, fields=["id", "name", "type", "enabled", "mac_address"])
```

## Common Field Filters (token optimization)

| Object Type | Minimal Fields |
|-------------|---------------|
| Sites | `["id", "name", "status", "slug"]` |
| Prefixes | `["id", "prefix", "vlan", "description"]` |
| VLANs | `["id", "name", "vid", "site", "description"]` |
| IPs | `["id", "address", "status", "dns_name", "description"]` |
| VMs | `["id", "name", "status", "primary_ip4", "site"]` |
