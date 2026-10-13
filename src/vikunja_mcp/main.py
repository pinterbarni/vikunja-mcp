"""Application entry point."""

from fastapi import FastAPI

from vikunja_mcp import __version__, health
from vikunja_mcp.config import Settings, get_settings
from vikunja_mcp.logging_config import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    """Builds the FastAPI application. Settings can be passed in, which keeps tests independent of env. """
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title="vikunja-mcp", version=__version__)
    app.state.settings = settings
    app.include_router(health.router)
    return app
