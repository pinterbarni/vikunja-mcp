"""Application entry point."""

import logging

from fastapi import FastAPI

from vikunja_mcp import __version__, health
from vikunja_mcp.config import Settings, get_settings
from vikunja_mcp.logging_config import configure_logging

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """
    Builds the FastAPI application.
    Settings can be passed in, which keeps tests independent of env.
    """
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    logger.info("vikunja-mcp %s starting, Vikunja at %s", __version__, settings.vikunja_url)

    app = FastAPI(title="vikunja-mcp", version=__version__)
    app.state.settings = settings
    app.include_router(health.router)
    return app
