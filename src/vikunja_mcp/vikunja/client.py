"""Client for the Vikunja REST API."""

import httpx

from vikunja_mcp.config import Settings
from vikunja_mcp.vikunja.models import Project


class HttpxVikunjaClient:
    def __init__(self, settings: Settings) -> None:
        self._http = httpx.AsyncClient(
            base_url=settings.vikunja_api_base_url,
            headers={"Authorization": f"Bearer {settings.vikunja_api_token.get_secret_value()}"},
            timeout=settings.vikunja_timeout_seconds,
        )

    async def list_projects(self) -> list[Project]:
        response = await self._http.get("/projects")
        response.raise_for_status()
        return [Project.model_validate(item) for item in response.json()]

    async def aclose(self) -> None:
        await self._http.aclose()
