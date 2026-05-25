#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$ROOT_DIR/feature_repo"

cleanup() {
    echo "Stopping servers..."
    kill "$FEAT_PID" "$REG_PID" 2>/dev/null || true
    wait "$FEAT_PID" "$REG_PID" 2>/dev/null || true
    echo "Done."
}
trap cleanup EXIT INT TERM

echo "Starting Feast Feature Server (MCP/SSE at /mcp) on port 6566..."
cd "$ROOT_DIR"
(uv run python scripts/serve_feature_uvicorn.py) &
FEAT_PID=$!

echo "Starting Feast Registry REST Server (MCP) on port 6567..."
(cd "$REPO_DIR" && uv run feast serve_registry --no-grpc --rest-api --rest-port 6567) &
REG_PID=$!

echo ""
echo "============================================"
echo "  Feature Server MCP:  http://localhost:6566/mcp"
echo "  Registry Server MCP: http://localhost:6567/mcp"
echo "============================================"
echo ""
echo "Press Ctrl+C to stop both servers."

wait
