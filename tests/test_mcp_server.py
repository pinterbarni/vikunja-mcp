from tests.fakes import FakeVikunjaClient
from vikunja_mcp.mcp_server import build_mcp_server


def test_server_is_named_after_the_project() -> None:
    mcp = build_mcp_server(FakeVikunjaClient())

    assert mcp.name == "vikunja-mcp"
