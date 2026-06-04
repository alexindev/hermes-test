---
name: api-integration-debugging
description: Systematic approach to debugging third-party API integrations — method mismatches, auth issues, rate limits, and silent failures.
category: devops
---

# API Integration Debugging

When an API integration isn't working, follow this systematic approach before assuming the server is broken.

## 1. Verify the API Contract

**ALWAYS check the official documentation first.** Common pitfalls:
- Wrong HTTP method (GET vs POST)
- Wrong content type (JSON vs form-data vs query params)
- Missing required headers
- Wrong parameter names or locations

```bash
# Test the exact documented request
curl -X GET 'https://api.example.com/endpoint?param=value' \
  -H 'Authorization: Bearer TOKEN'
```

## 2. Method Matrix Testing

If the documented method fails, test ALL reasonable variants:

| Variant | Example |
|---------|---------|
| GET with query params | `GET /path?key=val` |
| GET with JSON body | `GET /path` + `{"key": "val"}` |
| POST with JSON | `POST /path` + `Content-Type: application/json` |
| POST with form-data | `POST /path` + `Content-Type: application/x-www-form-urlencoded` |
| POST with different headers | `X-API-Key`, `Authorization`, etc. |

## 3. Parameter Variants

Test different parameter combinations:
- Required vs optional fields
- Empty values vs missing parameters
- Different data types (string vs integer)
- Parameter names (snake_case vs camelCase)

## 4. Silent Failure Detection

APIs may return `{"ok": true, "data": []}` when they should fail. Check:
- Response code vs response body
- Error messages in body vs HTTP status
- Rate limit headers
- Pagination tokens

## 5. Infrastructure Verification

Before blaming the API:
- Can you reach the endpoint? (`curl -v`)
- Is your authentication valid?
- Are there network restrictions (firewall, proxy)?
- Is the service actually running?

## 6. Logging Strategy

Add structured logging to track:
- Request URL + method
- Request headers
- Request body (redacted if sensitive)
- Response status + body
- Timing information

## Pitfalls

- **Assuming POST works when API needs GET** — always verify with curl first
- **Ignoring empty arrays** — `{"events": []}` might mean "no events" OR "auth failed silently"
- **Not checking all response fields** — some APIs put errors in unexpected places
- **Relying on SDKs without reading docs** — SDKs may wrap requests incorrectly
- **Going down rabbit holes** — When debugging a platform adapter issue, stay focused on the actual problem. Don't start reading unrelated adapters (e.g., don't read Telegram code when the bug is in VK Teams). Verify the hypothesis first, then dig deeper only if needed.