"""Task tools."""

from datetime import datetime

from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel

from vikunja_mcp.vikunja.client import VikunjaClient


class TaskSummary(BaseModel):
    id: int
    title: str
    done: bool
    priority: int
    project_id: int
    due_date: datetime | None


class TaskDetail(BaseModel):
    id: int
    title: str
    description: str
    done: bool
    priority: int
    percent_done: float
    project_id: int
    due_date: datetime | None
    start_date: datetime | None
    end_date: datetime | None
    created: datetime | None
    updated: datetime | None
    labels: list[str]
    assignees: list[str]


def register(mcp: MCPServer, client: VikunjaClient) -> None:
    @mcp.tool()
    async def list_tasks(
        project_id: int | None = None, include_done: bool = False
    ) -> list[TaskSummary]:
        """List Vikunja tasks.

        Only open tasks are returned, unless include_done is true.
        Pass project_id to limit the list to one project, use list_projects to find ids.
        due_date is null when a task has no due date.
        """
        tasks = await client.list_tasks(project_id=project_id, include_done=include_done)
        return [
            TaskSummary(
                id=t.id,
                title=t.title,
                done=t.done,
                priority=t.priority,
                project_id=t.project_id,
                due_date=t.due_date,
            )
            for t in tasks
        ]

    @mcp.tool()
    async def get_task(task_id: int) -> TaskDetail:
        """Get all details of one Vikunja task, including its description.

        Use list_tasks to find the task id.
        The description is HTML as written in Vikunja.
        Labels and assignees are returned as plain names.
        """
        t = await client.get_task(task_id)
        return TaskDetail(
            id=t.id,
            title=t.title,
            description=t.description,
            done=t.done,
            priority=t.priority,
            percent_done=t.percent_done,
            project_id=t.project_id,
            due_date=t.due_date,
            start_date=t.start_date,
            end_date=t.end_date,
            created=t.created,
            updated=t.updated,
            labels=[label.title for label in t.labels],
            assignees=[a.username for a in t.assignees],
        )
