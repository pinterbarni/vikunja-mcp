"""Application entry point."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from mcp.server.transport_security import TransportSecuritySettings

from vikunja_mcp import __version__, health
from vikunja_mcp.config import Settings, get_settings
from vikunja_mcp.logging_config import configure_logging
from vikunja_mcp.mcp_server import build_mcp_server
from vikunja_mcp.vikunja.client import HttpxVikunjaClient, VikunjaClient

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None, client: VikunjaClient | None = None) -> FastAPI:
    """Build the FastAPI application.

    Settings and the Vikunja client could be passed in so this keeps tests
    independent of the environment and the network.
    """
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    logger.info("starting vikunja-mcp version=%s vikunja_url=%s", __version__, settings.vikunja_url)
    vikunja = client or HttpxVikunjaClient(settings)

    mcp = build_mcp_server(vikunja)
    mcp_app = mcp.streamable_http_app(
        stateless_http=True,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True, allowed_hosts=settings.allowed_hosts
        ),
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
        try:
            async with mcp.session_manager.run():
                yield
        finally:
            await vikunja.aclose()

    app = FastAPI(title="vikunja-mcp", version=__version__, lifespan=lifespan)
    app.state.settings = settings
    app.state.vikunja = vikunja
    app.include_router(health.router)
    app.mount("/", mcp_app)
    return app
