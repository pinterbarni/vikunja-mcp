import json
from datetime import UTC, datetime

import httpx
import pytest
import respx

from vikunja_mcp.config import Settings
from vikunja_mcp.vikunja.client import HttpxVikunjaClient
from vikunja_mcp.vikunja.errors import VikunjaAPIError, VikunjaUnreachable

BASE = "https://vikunja.test.url/api/v1"


@pytest.fixture
async def client(settings: Settings):
    vikunja = HttpxVikunjaClient(settings)
    yield vikunja
    await vikunja.aclose()


@respx.mock
async def test_list_projects_parses_the_response(client: HttpxVikunjaClient) -> None:
    respx.get(f"{BASE}/projects").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"id": 1, "title": "Home", "owner": {"id": 9}},
                {"id": 2, "title": "Work"},
            ],
        )
    )

    projects = await client.list_projects()

    assert [(p.id, p.title) for p in projects] == [(1, "Home"), (2, "Work")]


@respx.mock
async def test_requests_carry_the_bearer_token(client: HttpxVikunjaClient) -> None:
    route = respx.get(f"{BASE}/projects").mock(return_value=httpx.Response(200, json=[]))

    await client.list_projects()

    assert route.calls.last.request.headers["authorization"] == "Bearer example-test-token"


@respx.mock
async def test_api_error_carries_status_and_message(client) -> None:
    respx.get(f"{BASE}/projects").mock(
        return_value=httpx.Response(401, json={"message": "invalid token"})
    )

    with pytest.raises(VikunjaAPIError) as excinfo:
        await client.list_projects()

    assert excinfo.value.status_code == 401
    assert "invalid token" in str(excinfo.value)


@respx.mock
async def test_api_error_without_json_body_uses_plain_text(client) -> None:
    respx.get(f"{BASE}/projects").mock(return_value=httpx.Response(502, text="Bad Gateway"))

    with pytest.raises(VikunjaAPIError) as excinfo:
        await client.list_projects()

    assert excinfo.value.status_code == 502
    assert "Bad Gateway" in str(excinfo.value)


@respx.mock
async def test_network_failure_becomes_unreachable(client) -> None:
    respx.get(f"{BASE}/projects").mock(side_effect=httpx.ConnectError("boom"))

    with pytest.raises(VikunjaUnreachable):
        await client.list_projects()


@respx.mock
async def test_list_projects_hides_archived_by_default(client: HttpxVikunjaClient) -> None:
    route = respx.get(f"{BASE}/projects").mock(return_value=httpx.Response(200, json=[]))

    await client.list_projects()

    assert "is_archived" not in route.calls.last.request.url.params


@respx.mock
async def test_list_projects_can_include_archived(client: HttpxVikunjaClient) -> None:
    route = respx.get(f"{BASE}/projects").mock(return_value=httpx.Response(200, json=[]))

    await client.list_projects(include_archived=True)

    assert route.calls.last.request.url.params["is_archived"] == "true"


@respx.mock
async def test_get_info_returns_version(client: HttpxVikunjaClient) -> None:
    respx.get(f"{BASE}/info").mock(return_value=httpx.Response(200, json={"version": "v2.7.0"}))

    info = await client.get_info()

    assert info.version == "v2.7.0"


@respx.mock
async def test_list_tasks_asks_for_open_tasks_by_default(client: HttpxVikunjaClient) -> None:
    route = respx.get(f"{BASE}/tasks").mock(
        return_value=httpx.Response(200, json=[{"id": 1, "title": "eat cake", "project_id": 2}])
    )

    tasks = await client.list_tasks()

    assert [(t.id, t.title) for t in tasks] == [(1, "eat cake")]
    assert route.calls.last.request.url.params["filter"] == "done = false"


@respx.mock
async def test_list_tasks_can_include_done_tasks(client: HttpxVikunjaClient) -> None:
    route = respx.get(f"{BASE}/tasks").mock(return_value=httpx.Response(200, json=[]))

    await client.list_tasks(include_done=True)

    assert "filter" not in route.calls.last.request.url.params


@respx.mock
async def test_list_tasks_can_be_limited_to_one_project(client: HttpxVikunjaClient) -> None:
    route = respx.get(f"{BASE}/projects/2/tasks").mock(return_value=httpx.Response(200, json=[]))

    await client.list_tasks(project_id=2)

    assert route.called


@respx.mock
async def test_get_task_returns_the_task(client: HttpxVikunjaClient) -> None:
    respx.get(f"{BASE}/tasks/7").mock(
        return_value=httpx.Response(
            200, json={"id": 7, "title": "Call the bank", "description": "<p>ask about fees</p>"}
        )
    )

    task = await client.get_task(7)

    assert (task.id, task.title) == (7, "Call the bank")


@respx.mock
async def test_get_task_raises_an_api_error_when_it_is_missing(client: HttpxVikunjaClient) -> None:
    respx.get(f"{BASE}/tasks/99").mock(
        return_value=httpx.Response(404, json={"message": "The task does not exist."})
    )

    with pytest.raises(VikunjaAPIError) as excinfo:
        await client.get_task(99)

    assert excinfo.value.status_code == 404


@respx.mock
async def test_create_task_puts_to_the_project_and_returns_the_task(client) -> None:
    route = respx.put(f"{BASE}/projects/3/tasks").mock(
        return_value=httpx.Response(
            201, json={"id": 77, "title": "Buy milk", "project_id": 3, "priority": 2}
        )
    )

    task = await client.create_task(
        3,
        "Buy milk",
        description="2 liters",
        due_date=datetime(2026, 10, 20, tzinfo=UTC),
        priority=2,
    )

    assert (task.id, task.title, task.project_id) == (77, "Buy milk", 3)
    assert json.loads(route.calls.last.request.content) == {
        "title": "Buy milk",
        "description": "2 liters",
        "due_date": "2026-10-20T00:00:00+00:00",
        "priority": 2,
    }


@respx.mock
async def test_create_task_leaves_out_the_due_date_when_there_is_none(client) -> None:
    route = respx.put(f"{BASE}/projects/3/tasks").mock(
        return_value=httpx.Response(201, json={"id": 78, "title": "Plain"})
    )

    await client.create_task(3, "Plain")

    assert "due_date" not in json.loads(route.calls.last.request.content)


@respx.mock
async def test_update_task_sends_the_whole_task_with_the_changes(client) -> None:
    respx.get(f"{BASE}/tasks/7").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 7,
                "title": "Old",
                "description": "<p>keep me</p>",
                "priority": 1,
                "project_id": 2,
                "labels": [{"id": 1, "title": "money"}],
            },
        )
    )
    route = respx.post(f"{BASE}/tasks/7").mock(
        return_value=httpx.Response(
            200, json={"id": 7, "title": "New", "description": "<p>keep me</p>", "project_id": 2}
        )
    )

    task = await client.update_task(7, {"title": "New"})

    assert task.title == "New"
    sent = json.loads(route.calls.last.request.content)
    assert sent["title"] == "New"
    assert sent["description"] == "<p>keep me</p>"
    assert sent["labels"] == [{"id": 1, "title": "money"}]


@respx.mock
async def test_update_task_does_not_post_when_the_task_is_missing(client) -> None:
    respx.get(f"{BASE}/tasks/99").mock(
        return_value=httpx.Response(404, json={"message": "The task does not exist."})
    )
    post = respx.post(f"{BASE}/tasks/99").mock(return_value=httpx.Response(200, json={}))

    with pytest.raises(VikunjaAPIError) as excinfo:
        await client.update_task(99, {"title": "x"})

    assert excinfo.value.status_code == 404
    assert not post.called
