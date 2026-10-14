"""Health"""

import logging
from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel

from vikunja_mcp import __version__
from vikunja_mcp.vikunja.client import VikunjaClient
from vikunja_mcp.vikunja.errors import VikunjaError

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    vikunja_reachable: bool
    vikunja_version: str | None = None


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    vikunja: VikunjaClient = request.app.state.vikunja
    try:
        info = await vikunja.get_info()
    except VikunjaError as exc:
        logger.warning("health check: vikunja not available error=%s", exc)
        return HealthResponse(status="degraded", version=__version__, vikunja_reachable=False)
    return HealthResponse(
        status="ok",
        version=__version__,
        vikunja_reachable=True,
        vikunja_version=info.version,
    )
