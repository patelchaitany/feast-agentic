# Feast Agentic — MCP Feature Store for Cursor

A sample [Feast](https://github.com/feast-dev/feast) feature store wired for **Model Context Protocol (MCP)** in Cursor: online feature serving plus registry introspection.

Watch the setup walkthrough: [`demo.mov`](demo.mov)

## What's included

- **Feature repo** (`feature_repo/`) — entities, feature views (including duplicate-schema views), Milvus online store
- **Feature server MCP** (port 6566) — `get_online_features`, `push`, `materialize`, etc.
- **Registry server MCP** (port 6567) — list/get entities, feature views, data sources, lineage, search
- **Cursor MCP config** — `.cursor/mcp.json`

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Feast **master** (installed via `pyproject.toml` git dependency — registry MCP is not in older PyPI releases)

## Quick start

```bash
git clone https://github.com/patelchaitany/feast-agentic.git
cd feast-agentic

uv sync
uv run python setup_data.py

./run.sh
```

In another terminal, verify MCP:

```bash
uv run python scripts/verify_mcp.py
```

## Cursor MCP

Use **only** the project config (`.cursor/mcp.json`). Do not duplicate `feast-features` in `~/.cursor/mcp.json`.

1. Start servers with `./run.sh`
2. **Settings → MCP** → enable `feast-features` and `feast-registry`
3. Toggle off/on or restart Cursor if tools do not appear

See [MCP_SETUP.md](MCP_SETUP.md) for transport notes and troubleshooting.

## Project layout

| Path | Purpose |
|------|---------|
| `feature_repo/features.py` | Entity and feature view definitions |
| `feature_repo/feature_store.yaml` | Registry, Milvus online store, MCP feature server |
| `setup_data.py` | Generate sample data, `feast apply`, materialize |
| `scripts/serve_feature_uvicorn.py` | Feature server (uvicorn, MCP-friendly) |
| `scripts/verify_mcp.py` | Check both MCP endpoints |
| `run.sh` | Start feature + registry servers |
| `demo.mov` | Demo video |

## Feature views

| View | Duplicate (same schema) | Entity |
|------|-------------------------|--------|
| `customer_profile` | `customer_profile_realtime` | `customer_id` |
| `knowledge_base` | `knowledge_base_v2` | `doc_id` |
| `agent_memory` | `agent_memory_long_term` | `customer_id` |

## Local Feast fork (optional)

To use a local Feast checkout instead of the git dependency, edit `pyproject.toml`:

```toml
"feast[mcp,milvus,grpcio] @ file:///path/to/feast",
```

Then run `uv sync`.
