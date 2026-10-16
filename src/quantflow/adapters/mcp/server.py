"""Transport-only MCP server. One read-only tool: hello(name, nonce)."""

from __future__ import annotations

import logging as _logging
import os
import time
import uuid
from contextlib import asynccontextmanager

import structlog
import uvicorn
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from quantflow.adapters.mcp.api_key import ApiKeyGate

log = structlog.get_logger("quantflow.mcp.server")

HOST = os.environ.get("POC_HOST", "127.0.0.1")
PORT = int(os.environ.get("POC_PORT", "8765"))


def create_app(api_key: str, public_host: str | None = None) -> Starlette:
    allowed_hosts = [f"127.0.0.1:{PORT}", f"localhost:{PORT}"]
    allowed_origins = [f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"]
    if public_host:
        allowed_hosts += [public_host, f"{public_host}:443"]
        allowed_origins.append(f"https://{public_host}")

    mcp = FastMCP(
        "QuantFlow",
        instructions="Transport POC. One read-only synthetic tool.",
        host=HOST,
        port=PORT,
        stateless_http=True,
        json_response=True,
        streamable_http_path="/mcp",
        max_request_body_size=8192,
        log_level="WARNING",
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=allowed_hosts,
            allowed_origins=allowed_origins,
        ),
    )

    ro = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )

    @mcp.tool(annotations=ro)
    async def hello(name: str, nonce: str) -> dict:
        """Echo name and nonce. Return a fresh server response_id."""
        if not name or len(name) > 64:
            raise ValueError("name must be 1-64 chars")
        if not nonce or len(nonce) < 16 or len(nonce) > 128:
            raise ValueError("nonce must be 16-128 chars")
        response_id = str(uuid.uuid4())
        log.info("tool=hello response_id=%s nonce_prefix=%s", response_id, nonce[:8])
        return {
            "message": f"hello {name}",
            "nonce": nonce,
            "response_id": response_id,
            "server_time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "auth_mode": "api_key",
            "synthetic": True,
        }

    mcp_app = mcp.streamable_http_app()

    @asynccontextmanager
    async def lifespan(app):
        async with mcp.session_manager.run():
            yield

    async def health(_request):
        return JSONResponse(
            {
                "status": "ok",
                "service": "quantflow-transport-poc",
                "synthetic_only": True,
            }
        )

    app = Starlette(
        routes=[Route("/healthz", health), Mount("/", app=mcp_app)],
        lifespan=lifespan,
    )
    return ApiKeyGate(app, api_key)


def main() -> None:
    _logging.basicConfig(level=_logging.INFO)
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
    )
    api_key = os.environ.get("POC_API_KEY")
    if not api_key:
        raise SystemExit("POC_API_KEY required")
    public_host = os.environ.get("POC_PUBLIC_HOST") or None
    app = create_app(api_key, public_host)
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        proxy_headers=False,
        access_log=False,
        limit_concurrency=16,
        timeout_keep_alive=5,
    )


if __name__ == "__main__":
    main()
