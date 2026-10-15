from datetime import UTC, datetime

from tests.fakes import FakeVikunjaClient
from vikunja_mcp.mcp_server import build_mcp_server
from vikunja_mcp.vikunja.models import Assignee, Label, Project, Task


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


async def test_get_task_returns_the_details() -> None:
    fake = FakeVikunjaClient(
        tasks=[
            Task(
                id=5,
                title="Call the bank",
                description="<p>ask about fees</p>",
                priority=3,
                percent_done=0.5,
                labels=[Label(id=1, title="money")],
                assignees=[Assignee(id=1, username="testuser")],
            )
        ]
    )

    result = await build_mcp_server(fake).call_tool("get_task", {"task_id": 5})
    task = result.structured_content

    assert task["title"] == "Call the bank"
    assert task["description"] == "<p>ask about fees</p>"
    assert task["percent_done"] == 0.5
    assert task["labels"] == ["money"]
    assert task["assignees"] == ["testuser"]
    assert task["due_date"] is None


async def test_create_task_uses_the_given_project() -> None:
    fake = FakeVikunjaClient(projects=[Project(id=1, title="Inbox"), Project(id=2, title="Home")])
    mcp = build_mcp_server(fake)

    result = await mcp.call_tool(
        "create_task", {"title": "Buy milk", "project_id": 2, "priority": 3}
    )

    assert result.structured_content["title"] == "Buy milk"
    assert result.structured_content["project_id"] == 2
    assert [t.title for t in fake.tasks] == ["Buy milk"]


async def test_create_task_without_a_project_goes_to_the_inbox() -> None:
    fake = FakeVikunjaClient(projects=[Project(id=2, title="Home"), Project(id=1, title="Inbox")])
    mcp = build_mcp_server(fake)

    result = await mcp.call_tool("create_task", {"title": "Call mum"})

    assert result.structured_content["project_id"] == 1


async def update(fake: FakeVikunjaClient, arguments: dict) -> dict:
    result = await build_mcp_server(fake).call_tool("update_task", arguments)
    return result.structured_content


async def test_update_task_changes_only_the_given_fields() -> None:
    fake = FakeVikunjaClient(tasks=[Task(id=1, title="Old", priority=2)])

    task = await update(fake, {"task_id": 1, "title": "New"})

    assert (task["title"], task["priority"]) == ("New", 2)
    assert fake.tasks[0].title == "New"


async def test_update_task_can_mark_a_task_done() -> None:
    fake = FakeVikunjaClient(tasks=[Task(id=1, title="Old")])

    task = await update(fake, {"task_id": 1, "done": True})

    assert task["done"] is True


async def test_update_task_can_set_a_due_date() -> None:
    fake = FakeVikunjaClient(tasks=[Task(id=1, title="Old")])

    task = await update(fake, {"task_id": 1, "due_date": "2026-10-30T09:00:00+00:00"})

    assert task["due_date"].startswith("2026-10-30")


async def test_update_task_can_clear_the_due_date() -> None:
    due = datetime(2026, 10, 22, 10, 0, tzinfo=UTC)
    fake = FakeVikunjaClient(tasks=[Task(id=1, title="Old", due_date=due)])

    task = await update(fake, {"task_id": 1, "clear_due_date": True})

    assert task["due_date"] is None


async def test_complete_task_marks_the_task_done() -> None:
    fake = FakeVikunjaClient(tasks=[Task(id=1, title="eat cake"), Task(id=2, title="buy milk")])

    result = await build_mcp_server(fake).call_tool("complete_task", {"task_id": 1})

    assert result.structured_content["done"] is True
    assert [t.done for t in fake.tasks] == [True, False]
