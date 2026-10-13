import httpx
import pytest
import respx

from vikunja_mcp.config import Settings
from vikunja_mcp.vikunja.client import HttpxVikunjaClient

BASE = "https://vikunja.test/api/v1"


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

    assert route.calls.last.request.headers["authorization"] == "Bearer test-token"