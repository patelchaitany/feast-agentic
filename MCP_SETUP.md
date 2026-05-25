# Feast MCP setup for Cursor

Based on [Feast MCP Feature Server docs](https://github.com/feast-dev/feast/blob/master/docs/reference/feature-servers/mcp-feature-server.md) and the [`mcp_feature_store` example](https://github.com/feast-dev/feast/blob/master/examples/mcp_feature_store/).

## Database SQL (`feast-db`)

Stdio MCP for schema exploration and read-only SQL (connection string + database type).

| Tool | Purpose |
|------|---------|
| `execute_sql` | Run SQL (`read_only=true` by default) |
| `list_database_tables` | List tables |
| `describe_database_table` | Column / PK / FK metadata |

Supported types: `postgres`, `mysql`, `sqlite`, `mssql`.

See [docs/DB_MCP.md](docs/DB_MCP.md). Toggle **feast-db** in **Settings → MCP** (no separate server process).

## Feature server (`feast-features`)

**`feature_repo/feature_store.yaml`** (required):

```yaml
feature_server:
  type: mcp
  enabled: true
  mcp_enabled: true
  mcp_transport: sse    # SSE at /mcp (same transport as registry; Cursor default)
```

**Cursor `.cursor/mcp.json`** — URL only (same pattern as `feast-registry`; do **not** set `"transport": "sse"`):

```json
{
  "mcpServers": {
    "feast-features": {
      "url": "http://127.0.0.1:6566/mcp"
    }
  }
}
```

Do **not** define `feast-features` in both `~/.cursor/mcp.json` and `.cursor/mcp.json` — that creates two duplicate entries in Cursor and both fail to load tools. Use only the project `.cursor/mcp.json` for this repo.

Do **not** set `"transport": "sse"` in `mcp.json`. Registry MCP works without a `transport` field; use the same for the feature server.

Start the feature server with **uvicorn** (not gunicorn):

```bash
uv run python scripts/serve_feature_uvicorn.py
```

## Registry server (`feast-registry`)

Registry MCP uses SSE at `/mcp` (separate process):

```json
{
  "mcpServers": {
    "feast-registry": {
      "url": "http://127.0.0.1:6567/mcp"
    }
  }
}
```

## Start both servers

```bash
./run.sh
```

Or manually:

```bash
uv run python scripts/serve_feature_uvicorn.py
# another terminal:
cd feature_repo && uv run feast serve_registry --no-grpc --rest-api --rest-port 6567
```

## Verify MCP before opening Cursor

```bash
cd /Users/chpatel/projects/feast-agentic
uv run python scripts/verify_mcp.py
```

## Claude Code (`.mcp.json` + `.claude/settings.local.json`)

Claude Code reads MCP from **project root `.mcp.json`**, not from `mcpServers` inside `settings.local.json` alone.

**`.mcp.json`** (stdio needs `"type": "stdio"`):

```json
{
  "mcpServers": {
    "feast-db": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "python", "-m", "mcp_db_server.server"],
      "env": {}
    },
    "feast-features": {
      "type": "sse",
      "url": "http://127.0.0.1:6566/mcp"
    },
    "feast-registry": {
      "type": "sse",
      "url": "http://127.0.0.1:6567/mcp"
    }
  }
}
```

**`.claude/settings.local.json`** (approve project MCP + tool permissions):

```json
{
  "enableAllProjectMcpServers": true,
  "enabledMcpjsonServers": ["feast-db", "feast-features", "feast-registry"],
  "permissions": {
    "allow": [
      "mcp__feast-db__*",
      "mcp__feast-features__*",
      "mcp__feast-registry__*"
    ],
    "deny": []
  }
}
```

Verify from project root:

```bash
claude mcp list
# feast-db should show: ✓ Connected, Type: stdio
```

If `uv` is not on Claude’s PATH, use the full path to `uv` in `.mcp.json` (`which uv`).

Add via CLI (optional):

```bash
claude mcp add --transport stdio --scope project feast-db -- uv run python -m mcp_db_server.server
claude mcp add --transport sse --scope project feast-features http://127.0.0.1:6566/mcp
claude mcp add --transport sse --scope project feast-registry http://127.0.0.1:6567/mcp
```

Without `"type": "sse"` on URL servers, Claude reports: `command: expected string, received undefined`.

## After changing config

1. Reinstall/sync Feast if you changed the local `feast` repo: `uv sync`
2. Restart both servers.
3. Update `~/.cursor/mcp.json` if you also defined `feast-features` there (remove `"transport": "sse"`).
4. In Cursor: **Settings → MCP** → toggle **feast-features** off/on (or restart Cursor).

## Transport reference

| Server | Feast setting | MCP URL | Cursor `mcp.json` |
|--------|---------------|---------|-------------------|
| Feature | `mcp_transport: http` | `http://127.0.0.1:6566/mcp` | URL only (no `transport`) |
| Feature | `mcp_transport: sse` | `http://127.0.0.1:6566/mcp` | URL only (no `transport`) |
| Registry | `registry.mcp.enabled: true` | `http://127.0.0.1:6567/mcp` | URL only |
