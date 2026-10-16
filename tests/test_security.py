import logging

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from vikunja_mcp.config import Settings
from vikunja_mcp.security import secure_mcp

ISSUER = "https://example.authkit.app"
PUBLIC_URL = "https://mcp.example.com/mcp"


def make_settings(**overrides):
    values = {"vikunja_url": "http://vikunja.test", "vikunja_api_token": "secret"}
    return Settings(_env_file=None, **{**values, **overrides})


async def inner(request):
    return PlainTextResponse("ok")


def make_client(**overrides) -> TestClient:
    app = Starlette(routes=[Route("/mcp", inner)])
    return TestClient(secure_mcp(app, make_settings(**overrides)))


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_without_any_auth_the_app_is_open_and_a_warning_is_logged(caplog):
    with caplog.at_level(logging.WARNING):
        client = make_client()

    assert client.get("/mcp").status_code == 200
    assert "open to anyone" in caplog.text


def test_static_token_only_mode_refuses_a_missing_token():
    client = make_client(mcp_auth_token="static-secret")

    assert client.get("/mcp").status_code == 401
    assert client.get("/mcp", headers=bearer("static-secret")).status_code == 200


def test_oauth_mode_points_to_the_metadata_when_the_token_is_missing():
    client = make_client(oauth_issuer=ISSUER, public_url=PUBLIC_URL)

    response = client.get("/mcp")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == (
        'Bearer resource_metadata="https://mcp.example.com'
        '/.well-known/oauth-protected-resource/mcp"'
    )


def test_oauth_mode_still_accepts_the_static_token():
    client = make_client(oauth_issuer=ISSUER, public_url=PUBLIC_URL, mcp_auth_token="static-secret")

    assert client.get("/mcp", headers=bearer("static-secret")).status_code == 200


def test_oauth_mode_refuses_garbage_without_calling_the_provider():
    client = make_client(oauth_issuer=ISSUER, public_url=PUBLIC_URL)

    assert client.get("/mcp", headers=bearer("not-a-jwt")).status_code == 401
