import pytest

from tests.fakes import FakeVikunjaClient
from vikunja_mcp.vikunja.errors import VikunjaUnreachable
from vikunja_mcp.vikunja.models import Project


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
