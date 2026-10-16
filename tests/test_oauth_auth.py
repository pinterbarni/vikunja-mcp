import logging
from typing import Any

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from vikunja_mcp.oauth import InvalidToken
from vikunja_mcp.oauth_auth import OAuthAuth

METADATA_URL = "https://mcp.example.com/.well-known/oauth-protected-resource"
ME = "user_01ABC"
SOMEONE_ELSE = "user_02XYZ"


class StubVerifier:
    def verify(self, token: str) -> dict[str, Any]:
        if token == "good-jwt":
            return {"sub": ME}
        if token == "other-jwt":
            return {"sub": SOMEONE_ELSE}
        raise InvalidToken("not a valid token")


async def inner(request):
    return PlainTextResponse("ok")


def make_client(
    static_token: str | None = None,
    allowed_subjects: tuple[str, ...] = (ME,),
) -> TestClient:
    app = Starlette(routes=[Route("/mcp", inner)])
    secured = OAuthAuth(
        app,
        verifier=StubVerifier(),
        metadata_url=METADATA_URL,
        static_token=static_token,
        allowed_subjects=allowed_subjects,
    )
    return TestClient(secured)


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_valid_access_token_is_let_through():
    response = make_client().get("/mcp", headers=bearer("good-jwt"))

    assert response.status_code == 200


def test_static_token_is_let_through_when_configured():
    response = make_client(static_token="secret").get("/mcp", headers=bearer("secret"))

    assert response.status_code == 200


def test_static_token_is_refused_when_not_configured():
    response = make_client().get("/mcp", headers=bearer("secret"))

    assert response.status_code == 401


def test_missing_token_is_refused_and_points_to_the_metadata():
    response = make_client().get("/mcp")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == f'Bearer resource_metadata="{METADATA_URL}"'
    assert response.json() == {"error": "unauthorized"}


def test_invalid_access_token_is_refused():
    response = make_client().get("/mcp", headers=bearer("bad-jwt"))

    assert response.status_code == 401


def test_other_auth_schemes_are_refused():
    response = make_client().get("/mcp", headers={"Authorization": "Basic good-jwt"})

    assert response.status_code == 401


def test_lifespan_events_pass_through():
    with make_client() as client:
        response = client.get("/mcp", headers=bearer("good-jwt"))

    assert response.status_code == 200


def test_valid_token_of_someone_not_on_the_list_is_forbidden():
    response = make_client().get("/mcp", headers=bearer("other-jwt"))

    assert response.status_code == 403
    assert response.json() == {"error": "forbidden"}


def test_empty_allowlist_lets_nobody_in_with_a_token():
    response = make_client(allowed_subjects=()).get("/mcp", headers=bearer("good-jwt"))

    assert response.status_code == 403


def test_static_token_does_not_need_the_allowlist():
    client = make_client(static_token="secret", allowed_subjects=())

    response = client.get("/mcp", headers=bearer("secret"))

    assert response.status_code == 200


def test_forbidden_subject_is_logged_without_the_token(caplog):
    with caplog.at_level(logging.WARNING):
        make_client().get("/mcp", headers=bearer("other-jwt"))

    assert SOMEONE_ELSE in caplog.text
    assert "other-jwt" not in caplog.text


def test_reason_for_an_invalid_token_is_logged_without_the_token(caplog):
    with caplog.at_level(logging.WARNING):
        make_client().get("/mcp", headers=bearer("bad-jwt"))

    assert "not a valid token" in caplog.text
    assert "bad-jwt" not in caplog.text
