from datetime import UTC, datetime

from tests.fakes import FakeVikunjaClient
from vikunja_mcp.mcp_server import build_mcp_server
from vikunja_mcp.vikunja.models import Task


def make_server():
    fake = FakeVikunjaClient(
        tasks=[
            Task(
                id=1,
                title="eat cake",
                project_id=2,
                priority=2,
                due_date=datetime(2026, 10, 22, 10, 0, tzinfo=UTC),
            ),
            Task(id=2, title="buy milk", project_id=1),
            Task(id=3, title="done already", project_id=2, done=True),
        ]
    )
    return build_mcp_server(fake)


async def call(arguments: dict) -> list[dict]:
    result = await make_server().call_tool("list_tasks", arguments)
    return result.structured_content["result"]


async def test_list_tasks_tool_is_registered() -> None:
    tools = await make_server().list_tools()

    assert "list_tasks" in [t.name for t in tools]


async def test_list_tasks_hides_done_tasks_by_default() -> None:
    tasks = await call({})

    assert [t["title"] for t in tasks] == ["eat cake", "buy milk"]


async def test_list_tasks_can_include_done_tasks() -> None:
    tasks = await call({"include_done": True})

    assert [t["title"] for t in tasks] == ["eat cake", "buy milk", "done already"]


async def test_list_tasks_can_be_limited_to_a_project() -> None:
    tasks = await call({"project_id": 1})

    assert [t["title"] for t in tasks] == ["buy milk"]


async def test_list_tasks_shows_due_date_or_null() -> None:
    tasks = {t["title"]: t for t in await call({})}

    assert tasks["eat cake"]["due_date"].startswith("2026-10-22")
    assert tasks["buy milk"]["due_date"] is None
