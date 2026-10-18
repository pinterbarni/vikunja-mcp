"""The MCP tools for projects."""

from mcp.server.mcpserver import MCPServer

from vikunja_mcp.tools.errors import friendly_errors
from vikunja_mcp.tools.projects.mappers import to_summary
from vikunja_mcp.tools.projects.models import ProjectSummary
from vikunja_mcp.vikunja.protocol import VikunjaClient


def register(mcp: MCPServer, client: VikunjaClient) -> None:
    @mcp.tool()
    @friendly_errors
    async def list_projects(include_archived: bool = False) -> list[ProjectSummary]:
        """List Vikunja projects. Archived projects are hidden unless requested."""
        projects = await client.list_projects(include_archived=include_archived)
        return [to_summary(project) for project in projects]
