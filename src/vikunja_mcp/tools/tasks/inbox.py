"""Finding the Inbox project."""

from mcp.server.mcpserver.exceptions import ToolError

from vikunja_mcp.constants import INBOX_PROJECT_NAME
from vikunja_mcp.vikunja.client import VikunjaClient


async def inbox_id(client: VikunjaClient) -> int:
    for project in await client.list_projects():
        if project.title.lower() == INBOX_PROJECT_NAME:
            return project.id
    raise ToolError("No project named Inbox was found. Pass a project_id (see list_projects).")
