"""X-Api-Key gate. Wraps any ASGI app."""

from __future__ import annotations

import hmac
import logging

from starlette.datastructures import Headers
from starlette.responses import JSONResponse

log = logging.getLogger(__name__)


class ApiKeyGate:
    def __init__(self, app, api_key: str) -> None:
        if not api_key or len(api_key) < 16:
            raise ValueError("api_key must be >= 16 chars")
        self.app = app
        self._expected = api_key.encode()

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            return await self.app(scope, receive, send)
        if scope["type"] != "http":
            return
        headers = Headers(scope=scope)
        provided = headers.get("x-api-key", "")
        if not provided:
            log.info("auth_denied reason=missing_key path=%s", scope["path"])
            return await self._reject(scope, receive, send, "AUTH_REQUIRED")
        if not hmac.compare_digest(provided.encode(), self._expected):
            log.info("auth_denied reason=invalid_key path=%s", scope["path"])
            return await self._reject(scope, receive, send, "INVALID_KEY")
        await self.app(scope, receive, send)

    async def _reject(self, scope, receive, send, code):
        resp = JSONResponse(
            {"error": code},
            status_code=401,
            headers={
                "WWW-Authenticate": "ApiKey",
                "Cache-Control": "no-store",
            },
        )
        await resp(scope, receive, send)
