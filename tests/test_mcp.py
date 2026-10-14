import json

from fastapi.testclient import TestClient

from tests.fakes import FakeVikunjaClient
from vikunja_mcp.config import Settings
from vikunja_mcp.main import create_app
from vikunja_mcp.vikunja.models import Project

HEADERS = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}


def rpc(client: TestClient, method: str, params: dict | None = None, id_: int = 1):
    body = {"jsonrpc": "2.0", "id": id_, "method": method, "params": params or {}}
    response = client.post("/mcp", headers=HEADERS, json=body)
    assert response.status_code == 200, response.text
    text = response.text
    if response.headers["content-type"].startswith("text/event-stream"):
        text = next(line[5:] for line in text.splitlines() if line.startswith("data:"))
    return json.loads(text)


def make_client(settings: Settings) -> TestClient:
    fake = FakeVikunjaClient(
        projects=[Project(id=1, title="Home"), Project(id=2, title="Old", is_archived=True)]
    )
    return TestClient(create_app(settings, client=fake))


def test_initialize_over_http(settings: Settings) -> None:
    with make_client(settings) as client:
        result = rpc(
            client,
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "0"},
            },
        )

    assert result["result"]["serverInfo"]["name"] == "vikunja-mcp"


def test_list_projects_tool_works_over_http(settings: Settings) -> None:
    with make_client(settings) as client:
        result = rpc(client, "tools/call", {"name": "list_projects", "arguments": {}}, 2)

    titles = [p["title"] for p in result["result"]["structuredContent"]["result"]]
    assert titles == ["Home"]


def test_unknown_host_is_rejected(settings: Settings) -> None:
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}

    with make_client(settings) as client:
        response = client.post("/mcp", headers={**HEADERS, "Host": "evil.example"}, json=body)

    assert response.status_code == 421
