from tests.fakes import FakeVikunjaClient
from vikunja_mcp.mcp_server import build_mcp_server
from vikunja_mcp.vikunja.models import Project


def make_server():
    fake = FakeVikunjaClient(
        projects=[Project(id=1, title="Home"), Project(id=2, title="Old", is_archived=True)]
    )
    return build_mcp_server(fake)


async def test_list_projects_tool_is_registered() -> None:
    tools = await make_server().list_tools()

    assert [t.name for t in tools] == ["list_projects"]


async def test_list_projects_hides_archived_by_default() -> None:
    result = await make_server().call_tool("list_projects", {})

    assert [p["title"] for p in result.structured_content["result"]] == ["Home"]


async def test_list_projects_can_include_archived() -> None:
    result = await make_server().call_tool("list_projects", {"include_archived": True})

    assert [p["archived"] for p in result.structured_content["result"]] == [False, True]
