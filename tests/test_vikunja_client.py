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
