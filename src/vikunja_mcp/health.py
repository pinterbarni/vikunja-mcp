"""Health endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel

from vikunja_mcp import __version__

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    """Report srv proc is up."""
    return HealthResponse(status="ok", version=__version__)
