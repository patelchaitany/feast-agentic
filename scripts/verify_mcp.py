#!/usr/bin/env python3
"""Verify Feast feature and registry MCP endpoints respond."""
import asyncio
import sys

from mcp import ClientSession
from mcp.client.sse import sse_client

FEATURE_URL = "http://127.0.0.1:6566/mcp"
REGISTRY_URL = "http://127.0.0.1:6567/mcp"


async def check_sse(name: str, url: str) -> int:
    async with sse_client(url, timeout=15) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            count = len(tools.tools)
            print(f"{name}: OK ({count} tools at {url})")
            return count


async def check_http(name: str, url: str) -> int:
    try:
        from mcp.client.streamable_http import streamablehttp_client
    except ImportError:
        from mcp.client.streamable_http import streamable_http_client as streamablehttp_client

    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            count = len(tools.tools)
            print(f"{name}: OK ({count} tools at {url}, streamable HTTP)")
            return count


async def main() -> int:
    errors = 0
    try:
        await check_sse("feast-features", FEATURE_URL)
    except Exception as sse_exc:
        print(f"feast-features SSE failed ({sse_exc}); trying HTTP...")
        try:
            await check_http("feast-features", FEATURE_URL)
        except Exception as exc:
            print(f"feast-features: FAIL ({exc})")
            errors += 1

    try:
        await check_sse("feast-registry", REGISTRY_URL)
    except Exception as exc:
        print(f"feast-registry: FAIL ({exc})")
        errors += 1

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
