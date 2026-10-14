"""MCP probe. Connects, lists tools, calls hello with a fresh nonce."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import secrets
import sys

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def run(url: str, api_key: str, nonce: str | None = None) -> dict:
    nonce = nonce or secrets.token_hex(16)
    headers = {"x-api-key": api_key}
    async with httpx.AsyncClient(
        headers=headers, timeout=15, follow_redirects=False
    ) as http:
        health_url = url.replace("/mcp", "/healthz")
        h = await http.get(health_url)
        if h.status_code != 200:
            raise RuntimeError(f"healthz returned {h.status_code}")
        async with streamable_http_client(url, http_client=http) as (r, w, _):
            async with ClientSession(r, w) as session:
                init = await session.initialize()
                tools = sorted(
                    t.name for t in (await session.list_tools()).tools
                )
                call = await session.call_tool(
                    "hello", {"name": "operator", "nonce": nonce}
                )
                if call.isError:
                    raise RuntimeError("hello tool returned error")
                payload = call.structuredContent or json.loads(
                    call.content[0].text
                )
                return {
                    "protocol_version": init.protocolVersion,
                    "tools": tools,
                    "hello": payload,
                }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://127.0.0.1:8765/mcp")
    p.add_argument("--api-key", default=None)
    p.add_argument("--nonce", default=None)
    args = p.parse_args()

    api_key = args.api_key or os.environ.get("POC_API_KEY")
    if not api_key:
        print("POC_API_KEY required", file=sys.stderr)
        sys.exit(2)

    try:
        result = asyncio.run(run(args.url, api_key, args.nonce))
    except Exception as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__}))
        sys.exit(1)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
