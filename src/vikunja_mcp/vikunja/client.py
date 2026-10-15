"""Vikunja client, httpx implementation."""

from typing import Protocol

import httpx

from vikunja_mcp.config import Settings
from vikunja_mcp.vikunja.errors import VikunjaAPIError, VikunjaUnreachable
from vikunja_mcp.vikunja.models import Project, ServerInfo, Task


class VikunjaClient(Protocol):
    """What the app needs from Vikunja - depend on this, not on httpx."""

    async def get_info(self) -> ServerInfo: ...

    async def list_projects(self, include_archived: bool = False) -> list[Project]: ...

    async def list_tasks(
        self, project_id: int | None = None, include_done: bool = False
    ) -> list[Task]: ...

    async def get_task(self, task_id: int) -> Task: ...

    async def aclose(self) -> None: ...


class HttpxVikunjaClient:
    def __init__(self, settings: Settings) -> None:
        self._http = httpx.AsyncClient(
            base_url=settings.vikunja_api_base_url,
            headers={"Authorization": f"Bearer {settings.vikunja_api_token.get_secret_value()}"},
            timeout=settings.vikunja_timeout_seconds,
        )

    async def list_projects(self, include_archived: bool = False) -> list[Project]:
        params = {"is_archived": "true"} if include_archived else None
        data = await self._get("/projects", params=params)
        return [Project.model_validate(item) for item in data]

    async def list_tasks(
        self, project_id: int | None = None, include_done: bool = False
    ) -> list[Task]:
        path = "/tasks" if project_id is None else f"/projects/{project_id}/tasks"
        params = None if include_done else {"filter": "done = false"}
        data = await self._get(path, params=params)
        return [Task.model_validate(item) for item in data]

    async def get_task(self, task_id: int) -> Task:
        return Task.model_validate(await self._get(f"/tasks/{task_id}"))

    async def get_info(self) -> ServerInfo:
        return ServerInfo.model_validate(await self._get("/info"))

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _get(self, path: str, params: dict[str, str] | None = None):
        try:
            response = await self._http.get(path, params=params)
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
