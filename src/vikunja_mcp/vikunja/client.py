"""Vikunja client, httpx implementation."""

from datetime import datetime
from typing import Any

import httpx

from vikunja_mcp.config import Settings
from vikunja_mcp.vikunja.errors import VikunjaAPIError, VikunjaUnreachable
from vikunja_mcp.vikunja.models import Project, ServerInfo, Task


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

    async def create_task(
        self,
        project_id: int,
        title: str,
        description: str = "",
        due_date: datetime | None = None,
        priority: int = 0,
    ) -> Task:
        body: dict[str, Any] = {"title": title, "description": description, "priority": priority}
        if due_date is not None:
            body["due_date"] = due_date.isoformat()
        return Task.model_validate(
            await self._request("PUT", f"/projects/{project_id}/tasks", json=body)
        )

    async def update_task(self, task_id: int, changes: dict[str, Any]) -> Task:
        current = await self._get(f"/tasks/{task_id}")
        updated = await self._request("POST", f"/tasks/{task_id}", json={**current, **changes})
        return Task.model_validate(updated)

    async def get_info(self) -> ServerInfo:
        return ServerInfo.model_validate(await self._get("/info"))

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _get(self, path: str, params: dict[str, str] | None = None) -> Any:
        return await self._request("GET", path, params=params)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        try:
            response = await self._http.request(method, path, params=params, json=json)
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
