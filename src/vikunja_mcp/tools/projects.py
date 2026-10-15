"""Project tools."""

from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel

from vikunja_mcp.tools.errors import friendly_errors
from vikunja_mcp.vikunja.client import VikunjaClient


class ProjectSummary(BaseModel):
    id: int
    title: str
    archived: bool


def register(mcp: MCPServer, client: VikunjaClient) -> None:
    @mcp.tool()
    @friendly_errors
    async def list_projects(include_archived: bool = False) -> list[ProjectSummary]:
        """List Vikunja projects. Archived projects are hidden unless requested."""
        projects = await client.list_projects(include_archived=include_archived)
        return [ProjectSummary(id=p.id, title=p.title, archived=p.is_archived) for p in projects]
