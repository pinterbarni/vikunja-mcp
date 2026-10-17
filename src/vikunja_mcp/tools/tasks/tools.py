"""The MCP tools for tasks."""

from datetime import datetime
from typing import Any

from mcp.server.mcpserver import MCPServer

from vikunja_mcp.constants import NO_DATE
from vikunja_mcp.tools.errors import friendly_errors
from vikunja_mcp.tools.tasks.inbox import inbox_id
from vikunja_mcp.tools.tasks.mappers import to_detail, to_summary
from vikunja_mcp.tools.tasks.models import TaskDetail, TaskSummary
from vikunja_mcp.vikunja.client import VikunjaClient


def register(mcp: MCPServer, client: VikunjaClient) -> None:
    @mcp.tool()
    @friendly_errors
    async def list_tasks(
        project_id: int | None = None, include_done: bool = False
    ) -> list[TaskSummary]:
        """
        List Vikunja tasks.
        Only open tasks are returned, unless include_done is true.
        Pass project_id to limit the list to one project, use list_projects to find ids.
        due_date is null when a task has no due date.
        """
        tasks = await client.list_tasks(project_id=project_id, include_done=include_done)
        return [to_summary(task) for task in tasks]

    @mcp.tool()
    @friendly_errors
    async def get_task(task_id: int) -> TaskDetail:
        """
        Get all details of one Vikunja task, including its description.
        Use list_tasks to find the task id.
        The description is HTML as written in Vikunja.
        Labels and assignees are returned as plain names.
        """
        return to_detail(await client.get_task(task_id))

    @mcp.tool()
    @friendly_errors
    async def create_task(
        title: str,
        project_id: int | None = None,
        description: str = "",
        due_date: datetime | None = None,
        priority: int = 0,
    ) -> TaskDetail:
        """
        Create a task. Without project_id it goes to the Inbox.
        priority runs from 0 (none) to 5 (most urgent).
        due_date is an ISO 8601 date and time.
        """
        if project_id is None:
            project_id = await inbox_id(client)
        task = await client.create_task(project_id, title, description, due_date, priority)
        return to_detail(task)

    @mcp.tool()
    @friendly_errors
    async def update_task(
        task_id: int,
        title: str | None = None,
        description: str | None = None,
        due_date: datetime | None = None,
        clear_due_date: bool = False,
        priority: int | None = None,
        done: bool | None = None,
    ) -> TaskDetail:
        """
        Change a task. Only the fields you pass are changed, everything else stays.
        Use list_tasks to find the task id.
        Set done to true to complete a task, or to false to reopen it.
        priority runs from 0 (none) to 5 (most urgent).
        due_date is an ISO 8601 date and time. Set clear_due_date to true to remove the due date.
        """
        given = {"title": title, "description": description, "priority": priority, "done": done}
        changes: dict[str, Any] = {k: v for k, v in given.items() if v is not None}
        if due_date is not None:
            changes["due_date"] = due_date.isoformat()
        if clear_due_date:
            changes["due_date"] = NO_DATE
        return to_detail(await client.update_task(task_id, changes))

    @mcp.tool()
    @friendly_errors
    async def complete_task(task_id: int) -> TaskDetail:
        """
        Mark a task as done. Use list_tasks to find the task id.
        To reopen a task, use update_task with done set to false.
        """
        return to_detail(await client.update_task(task_id, {"done": True}))
