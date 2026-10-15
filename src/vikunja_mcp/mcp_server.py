"""MCP server construct, tools in vikunja_mcp.tools."""

from mcp.server.mcpserver import MCPServer

from vikunja_mcp.tools import projects, tasks
from vikunja_mcp.vikunja.client import VikunjaClient


def build_mcp_server(client: VikunjaClient) -> MCPServer:
    mcp = MCPServer("vikunja-mcp")
    projects.register(mcp, client)
    tasks.register(mcp, client)
    return mcp
