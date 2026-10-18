"""What the app needs from Vikunja. Depend on this, not on httpx."""

from datetime import datetime
from typing import Any, Protocol

from vikunja_mcp.vikunja.models import Project, ServerInfo, Task


class VikunjaClient(Protocol):
    async def get_info(self) -> ServerInfo: ...

    async def list_projects(self, include_archived: bool = False) -> list[Project]: ...

    async def list_tasks(
        self, project_id: int | None = None, include_done: bool = False
    ) -> list[Task]: ...

    async def get_task(self, task_id: int) -> Task: ...

    async def create_task(
        self,
        project_id: int,
        title: str,
        description: str = "",
        due_date: datetime | None = None,
        priority: int = 0,
    ) -> Task: ...

    async def update_task(self, task_id: int, changes: dict[str, Any]) -> Task: ...

    async def aclose(self) -> None: ...
