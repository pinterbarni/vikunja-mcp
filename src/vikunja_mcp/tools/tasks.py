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
