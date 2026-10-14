"""Vikunja client, httpx implementation."""

import httpx

from vikunja_mcp.config import Settings
from vikunja_mcp.vikunja.errors import VikunjaAPIError, VikunjaUnreachable
from vikunja_mcp.vikunja.models import Project


class HttpxVikunjaClient:
    def __init__(self, settings: Settings) -> None:
        self._http = httpx.AsyncClient(
            base_url=settings.vikunja_api_base_url,
            headers={"Authorization": f"Bearer {settings.vikunja_api_token.get_secret_value()}"},
            timeout=settings.vikunja_timeout_seconds,
        )

    async def list_projects(self) -> list[Project]:
        data = await self._get("/projects")
        return [Project.model_validate(item) for item in data]

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _get(self, path: str):
        try:
            response = await self._http.get(path)
        except httpx.HTTPError as exc:
            raise VikunjaUnreachable(f"Could not reach Vikunja: {exc}") from exc
        if response.is_error:
            raise VikunjaAPIError(response.status_code, _error_message(response))
        return response.json()


def _error_message(response: httpx.Response) -> str:
    try:
        return str(response.json().get("message", response.text))
    except ValueError:
        return response.text
