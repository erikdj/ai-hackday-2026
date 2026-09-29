# Judge dashboard

Read-only FastAPI view of Safe Scribe lineage for the live demo (`python -m hallway.dashboard.app`, port 8090).

## MCP endpoint

External agent platforms call lineage tools over Streamable HTTP (POST only; no SSE).

- URL: `http://<host>:8090/mcp`
- From a Docker container on the same machine: `http://host.docker.internal:8090/mcp`
- Transport: `http` (Streamable HTTP, POST only)
- Health: `GET /mcp/health`
- Tools: `who_saw_identifiers`, `open_followups_by_owner`, `patient_history`

```bash
curl -s -X POST http://127.0.0.1:8090/mcp \
  -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"demo","version":"0"}}}'

curl -s -X POST http://127.0.0.1:8090/mcp \
  -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"who_saw_identifiers","arguments":{}}}'
```
