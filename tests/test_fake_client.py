import pytest

from tests.fakes import FakeVikunjaClient
from vikunja_mcp.vikunja.errors import VikunjaAPIError, VikunjaUnreachable
from vikunja_mcp.vikunja.models import Project, Task


async def test_fake_hides_archived_projects_by_default() -> None:
    fake = FakeVikunjaClient(
        projects=[Project(id=1, title="Home"), Project(id=2, title="Old", is_archived=True)]
    )

    assert [p.id for p in await fake.list_projects()] == [1]
    assert [p.id for p in await fake.list_projects(include_archived=True)] == [1, 2]


async def test_fake_can_be_told_to_fail() -> None:
    fake = FakeVikunjaClient(error=VikunjaUnreachable("down"))

    with pytest.raises(VikunjaUnreachable):
        await fake.get_info()


async def test_fake_lists_open_tasks_and_can_limit_to_a_project() -> None:
    fake = FakeVikunjaClient(
        tasks=[
            Task(id=1, title="a", project_id=1),
            Task(id=2, title="b", project_id=2),
            Task(id=3, title="c", project_id=2, done=True),
        ]
    )

    assert [t.id for t in await fake.list_tasks()] == [1, 2]
    assert [t.id for t in await fake.list_tasks(project_id=2)] == [2]
    assert [t.id for t in await fake.list_tasks(project_id=2, include_done=True)] == [2, 3]


async def test_fake_returns_a_task_by_id() -> None:
    fake = FakeVikunjaClient(tasks=[Task(id=1, title="a"), Task(id=2, title="b")])

    assert (await fake.get_task(2)).title == "b"


async def test_fake_raises_a_404_for_an_unknown_task() -> None:
    fake = FakeVikunjaClient()

    with pytest.raises(VikunjaAPIError) as excinfo:
        await fake.get_task(99)

    assert excinfo.value.status_code == 404


async def test_fake_creates_a_task_with_the_next_id() -> None:
    fake = FakeVikunjaClient(tasks=[Task(id=5, title="Old")])

    task = await fake.create_task(2, "Buy milk", priority=3)

    assert (task.id, task.title, task.project_id, task.priority) == (6, "Buy milk", 2, 3)
    assert task in fake.tasks
