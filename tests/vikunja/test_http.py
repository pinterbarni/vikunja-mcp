import json

import httpx
import pytest
import respx

from vikunja_mcp.vikunja.errors import VikunjaAPIError, VikunjaUnreachable
from vikunja_mcp.vikunja.http import VikunjaHttp

BASE_URL = "https://vikunja.test/api/v1"


@pytest.fixture
async def vikunja_http():
    client = httpx.AsyncClient(base_url=BASE_URL)
    yield VikunjaHttp(client)
    await client.aclose()


@respx.mock
async def test_returns_the_json_body(vikunja_http):
    respx.get(f"{BASE_URL}/projects").mock(return_value=httpx.Response(200, json=[{"id": 1}]))

    assert await vikunja_http.request("GET", "/projects") == [{"id": 1}]


@respx.mock
async def test_sends_params_and_json_body(vikunja_http):
    route = respx.post(f"{BASE_URL}/tasks/1").mock(return_value=httpx.Response(200, json={}))

    await vikunja_http.request(
        "POST", "/tasks/1", params={"filter": "done = false"}, json={"title": "x"}
    )

    request = route.calls.last.request
    assert request.url.params["filter"] == "done = false"
    assert json.loads(request.content) == {"title": "x"}


@respx.mock
async def test_network_failure_becomes_unreachable(vikunja_http):
    respx.get(f"{BASE_URL}/projects").mock(side_effect=httpx.ConnectTimeout("slow"))

    with pytest.raises(VikunjaUnreachable, match="Could not reach Vikunja"):
        await vikunja_http.request("GET", "/projects")


@respx.mock
async def test_error_status_carries_the_message_from_vikunja(vikunja_http):
    respx.get(f"{BASE_URL}/tasks/9").mock(
        return_value=httpx.Response(404, json={"message": "The task does not exist."})
    )

    with pytest.raises(VikunjaAPIError) as raised:
        await vikunja_http.request("GET", "/tasks/9")

    assert raised.value.status_code == 404
    assert raised.value.message == "The task does not exist."


@respx.mock
async def test_error_without_a_message_field_uses_the_body_text(vikunja_http):
    response = httpx.Response(500, json={"code": 1})
    respx.get(f"{BASE_URL}/tasks/9").mock(return_value=response)

    with pytest.raises(VikunjaAPIError) as raised:
        await vikunja_http.request("GET", "/tasks/9")

    assert raised.value.message == response.text


@respx.mock
async def test_error_with_a_plain_text_body_uses_the_text(vikunja_http):
    respx.get(f"{BASE_URL}/tasks/9").mock(return_value=httpx.Response(502, text="Bad gateway"))

    with pytest.raises(VikunjaAPIError) as raised:
        await vikunja_http.request("GET", "/tasks/9")

    assert raised.value.message == "Bad gateway"
