"""MCP server construct, tools in vikunja_mcp.tools."""

from mcp.server.mcpserver import MCPServer

from vikunja_mcp.vikunja.client import VikunjaClient


def build_mcp_server(client: VikunjaClient) -> MCPServer:
    return MCPServer("vikunja-mcp")
