"""Pick the protection for /mcp from the settings."""

import logging

from starlette.types import ASGIApp

from vikunja_mcp.auth import BearerTokenAuth
from vikunja_mcp.config import Settings
from vikunja_mcp.oauth import TokenVerifier, jwks_key_resolver
from vikunja_mcp.oauth_auth import OAuthAuth
from vikunja_mcp.well_known import metadata_url

logger = logging.getLogger(__name__)


def secure_mcp(app: ASGIApp, settings: Settings) -> ASGIApp:
    """OAuth (plus the static token) if configured, else the static token, else open."""
    static_token = settings.mcp_auth_token.get_secret_value() if settings.mcp_auth_token else None
    if settings.oauth_issuer and settings.public_url:
        verifier = TokenVerifier(
            issuer=settings.oauth_issuer,
            audience=settings.public_url,
            resolve_key=jwks_key_resolver(settings.oauth_issuer),
        )
        return OAuthAuth(
            app,
            verifier=verifier,
            metadata_url=metadata_url(settings.public_url),
            allowed_subjects=settings.oauth_allowed_subjects,
            static_token=static_token,
        )
    if static_token:
        return BearerTokenAuth(app, static_token)
    logger.warning("MCP_AUTH_TOKEN is not set, /mcp is open to anyone who can reach it")
    return app
