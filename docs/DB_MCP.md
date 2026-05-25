# feast-db MCP server

SQL tools for agents building Feast feature views from an existing database.

## Tools

| Tool | Purpose |
|------|---------|
| `execute_sql` | Run SQL (read-only by default) |
| `list_database_tables` | List tables by schema |
| `describe_database_table` | Columns, PKs, FKs for one table |

## Supported `database_type` values

- `postgres` / `postgresql`
- `mysql`
- `sqlite`
- `mssql` / `sqlserver`

## Connection string examples

| Type | Example |
|------|---------|
| Postgres | `postgresql://user:pass@localhost:5432/analytics` or `user:pass@localhost:5432/analytics` |
| MySQL | `mysql://user:pass@localhost:3306/analytics` or `user:pass@localhost:3306/analytics` |
| SQLite | `sqlite:///path/to/db.sqlite` or `/path/to/db.sqlite` |
| SQL Server | `user:pass@host:1433/dbname` |

Pass credentials in the tool call only — do not commit them to git. Prefer environment variables in agent prompts.

## Claude Code setup

Project **`.mcp.json`** must include `feast-db` with `"type": "stdio"`. Approve it in **`.claude/settings.local.json`** (`enableAllProjectMcpServers`, `mcp__feast-db__*` permissions). Run `claude mcp list` — expect `feast-db: ✓ Connected`.

## Cursor setup

Already in `.cursor/mcp.json`:

```json
"feast-db": {
  "command": "uv",
  "args": ["run", "python", "-m", "mcp_db_server.server"]
}
```

Toggle **feast-db** on in **Settings → MCP**.

## Example agent flow

1. **feast-db** `list_database_tables` → find training tables  
2. **feast-db** `describe_database_table` → pick entity key, timestamp, feature columns  
3. Edit `feature_repo/features.py` + `feast apply`  
4. **feast-registry** / **feast-features** MCP for registry and serving  

### Example tool inputs

```json
{
  "connection_string": "user:pass@localhost:5432/analytics",
  "database_type": "postgres",
  "sql": "SELECT customer_id, event_timestamp, total_spend FROM customer_features LIMIT 5"
}
```

## Run manually

```bash
uv run python -m mcp_db_server.server
# or
uv run feast-db-mcp
```

## Safety

- `execute_sql` defaults to **read_only=true** (SELECT / WITH / SHOW / DESCRIBE / EXPLAIN / PRAGMA only).
- Set `read_only=false` only when the agent must run writes (DDL/DML).
- Result rows are capped with `limit` (default 100).
