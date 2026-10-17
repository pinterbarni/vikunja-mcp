"""ASGI check for /mcp: accept an OAuth access token or the static token."""

import asyncio
import logging
import secrets
from collections.abc import Collection
from typing import Any, Protocol

from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from vikunja_mcp.auth.jwt_verifier import InvalidToken

logger = logging.getLogger(__name__)


class Verifier(Protocol):
    def verify(self, token: str) -> dict[str, Any]: ...


class OAuthAuth:
    def __init__(
        self,
        app: ASGIApp,
        *,
        verifier: Verifier,
        metadata_url: str,
        allowed_subjects: Collection[str],
        static_token: str | None = None,
    ) -> None:
        self.app = app
        self._verifier = verifier
        self._metadata_url = metadata_url
        self._allowed_subjects = frozenset(allowed_subjects)
        self._static_token = static_token

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        token = _bearer_token(scope)
        status = 401 if token is None else await self._check(token)
        if status == 200:
            await self.app(scope, receive, send)
            return
        await self._reject(status)(scope, receive, send)

    async def _check(self, token: str) -> int:
        """Return 200 when allowed, 401 when the token is not valid, 403 when not on the list."""
        if self._static_token is not None and secrets.compare_digest(
            token.encode(), self._static_token.encode()
        ):
            return 200
        try:
            # The key lookup is a blocking network call on a cold cache.
            claims = await asyncio.to_thread(self._verifier.verify, token)
        except InvalidToken as error:
            logger.warning("Rejected an access token: %s", error)
            return 401
        subject = claims["sub"]
        if subject not in self._allowed_subjects:
            logger.warning("Rejected a valid token from a subject that is not allowed: %s", subject)
            return 403
        return 200

    def _reject(self, status: int) -> JSONResponse:
        if status == 403:
            return JSONResponse({"error": "forbidden"}, status_code=403)
        return JSONResponse(
            {"error": "unauthorized"},
            status_code=401,
            headers={"WWW-Authenticate": f'Bearer resource_metadata="{self._metadata_url}"'},
        )


def _bearer_token(scope: Scope) -> str | None:
    value = Headers(scope=scope).get("authorization")
    if value is None:
        return None
    scheme, _, token = value.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()
