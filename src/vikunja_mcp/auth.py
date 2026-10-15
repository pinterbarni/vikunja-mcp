"""Shared-secret authentication for the MCP endpoint."""

import secrets

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


class BearerTokenAuth:
    """ASGI wrapper: only requests with the expected bearer token reach the app."""

    def __init__(self, app: ASGIApp, token: str) -> None:
        self._app = app
        self._token = token.encode()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and not self._is_allowed(scope):
            response = JSONResponse(
                {"error": "unauthorized"},
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )
            await response(scope, receive, send)
            return
        await self._app(scope, receive, send)

    def _is_allowed(self, scope: Scope) -> bool:
        value = dict(scope["headers"]).get(b"authorization", b"")
        scheme, _, given = value.partition(b" ")
        return scheme.lower() == b"bearer" and secrets.compare_digest(given, self._token)
