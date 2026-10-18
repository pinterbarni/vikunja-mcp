from fastapi import FastAPI
from fastapi.testclient import TestClient

from vikunja_mcp.auth.static_token import BearerTokenAuth


def make_client() -> TestClient:
    inner = FastAPI()

    @inner.get("/ping")
    async def ping() -> dict[str, bool]:
        return {"ok": True}

    return TestClient(BearerTokenAuth(inner, "s3cret"))


def test_a_request_without_a_token_is_rejected() -> None:
    response = make_client().get("/ping")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_a_wrong_token_is_rejected() -> None:
    response = make_client().get("/ping", headers={"Authorization": "Bearer nope"})

    assert response.status_code == 401


def test_another_auth_scheme_is_rejected() -> None:
    response = make_client().get("/ping", headers={"Authorization": "Basic s3cret"})

    assert response.status_code == 401


def test_the_right_token_gets_through() -> None:
    response = make_client().get("/ping", headers={"Authorization": "Bearer s3cret"})

    assert response.status_code == 200
    assert response.json() == {"ok": True}
