# Ad-hoc MCP via JSON-RPC (stdio)

When the built-in Hermes MCP client is unavailable or you need to test/debug an MCP server directly, you can communicate with it via raw JSON-RPC over stdin/stdout using `subprocess.Popen`.

## Pattern

```python
import subprocess, json

proc = subprocess.Popen(
    ['uvx', 'postgres-mcp', '--access-mode=restricted'],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    env={**__import__('os').environ, 'DATABASE_URI': 'postgresql://postgres:postgres@host.docker.internal:6432/bigdata'}
)

# 1. Initialize
init_msg = json.dumps({
    'jsonrpc': '2.0', 'id': 1,
    'method': 'initialize',
    'params': {
        'protocolVersion': '2024-11-05',
        'capabilities': {},
        'clientInfo': {'name': 'test', 'version': '1.0'}
    }
}) + '\n'
proc.stdin.write(init_msg.encode())
proc.stdin.flush()
response = proc.stdout.readline().decode()

# 2. List tools
list_tools = json.dumps({
    'jsonrpc': '2.0', 'id': 2,
    'method': 'tools/list', 'params': {}
}) + '\n'
proc.stdin.write(list_tools.encode())
proc.stdin.flush()
response = proc.stdout.readline().decode()

# 3. Call a tool (e.g. execute_sql)
# CRITICAL: method is "tools/call" (NOT "call_tool"), params (not arguments at top level)
call = json.dumps({
    'jsonrpc': '2.0', 'id': 3,
    'method': 'tools/call',
    'params': {
        'name': 'execute_sql',
        'arguments': {'sql': 'SELECT count(*) FROM products'}
    }
}) + '\n'
proc.stdin.write(call.encode())
proc.stdin.flush()
response = proc.stdout.readline().decode()
result = json.loads(response)

# Response shape: {"result": {"content": [{"text": "[{'count': 2386}]"}]}}
# OR: {"error": {"code": -32602, "message": "..."}}
proc.terminate()
```

## Key details

- Each message is JSON-RPC 2.0, terminated by a newline (`\n`).
- Read one line per response — `postgres-mcp` returns one JSON object per line.
- **Method is `tools/call`**, NOT `call_tool`. Using `call_tool` returns `-32602 Invalid request parameters`.
- Parameters go under `params` key, NOT top-level `arguments`.
- Parameter name for `execute_sql` is `sql`, NOT `query`.
- Parameter name for `list_objects` is `schema_name`, NOT `schema`.
- `postgres-mcp` returns Python objects (UUID, Decimal) serialized as strings in the text field. Parse with `ast.literal_eval` if needed.
- For error responses, check `result.get('error')` — codes like `-32602` mean invalid params.

## When to use

- Testing MCP servers before configuring them in `~/.hermes/config.yaml`.
- Debugging connection issues when the Hermes MCP client reports generic errors.
- One-off queries when you don't want to set up a full MCP config.
- Verifying that `DATABASE_URI` is correct before restarting Hermes.
