"""In-memory stubs for Vikunja, used by tests instead of the network."""

from datetime import datetime
from typing import Any

from vikunja_mcp.vikunja.errors import VikunjaAPIError
from vikunja_mcp.vikunja.models import Project, ServerInfo, Task


class FakeVikunjaClient:
    def __init__(
        self,
        projects: list[Project] | None = None,
        version: str = "v0.0.0-fake",
        error: Exception | None = None,
        tasks: list[Task] | None = None,
    ) -> None:
        self.projects = projects or []
        self.tasks = tasks or []
        self.version = version
        self.error = error
        self.closed = False

    async def get_info(self) -> ServerInfo:
        self._fail_if_told_to()
        return ServerInfo(version=self.version)

    async def list_projects(self, include_archived: bool = False) -> list[Project]:
        self._fail_if_told_to()
        return [p for p in self.projects if include_archived or not p.is_archived]

    async def list_tasks(
        self, project_id: int | None = None, include_done: bool = False
    ) -> list[Task]:
        self._fail_if_told_to()
        return [
            t
            for t in self.tasks
            if (project_id is None or t.project_id == project_id) and (include_done or not t.done)
        ]

    async def get_task(self, task_id: int) -> Task:
        self._fail_if_told_to()
        for task in self.tasks:
            if task.id == task_id:
                return task
        raise VikunjaAPIError(404, "The task does not exist.")

    async def create_task(
        self,
        project_id: int,
        title: str,
        description: str = "",
        due_date: datetime | None = None,
        priority: int = 0,
    ) -> Task:
        self._fail_if_told_to()
        task = Task(
            id=max((t.id for t in self.tasks), default=0) + 1,
            title=title,
            description=description,
            project_id=project_id,
            due_date=due_date,
            priority=priority,
        )
        self.tasks.append(task)
        return task

    async def update_task(self, task_id: int, changes: dict[str, Any]) -> Task:
        self._fail_if_told_to()
        task = await self.get_task(task_id)
        updated = Task.model_validate({**task.model_dump(), **changes})
        self.tasks = [updated if t.id == task_id else t for t in self.tasks]
        return updated

    async def aclose(self) -> None:
        self.closed = True

    def _fail_if_told_to(self) -> None:
        if self.error is not None:
            raise self.error
