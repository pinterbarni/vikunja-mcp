from fastapi import FastAPI
from fastapi.testclient import TestClient

from vikunja_mcp.well_known import build_router, metadata_url

ISSUER = "https://example.authkit.app"
PUBLIC_URL = "https://mcp.example.com/mcp"


def make_client() -> TestClient:
    app = FastAPI()
    app.include_router(build_router(public_url=PUBLIC_URL, issuer=ISSUER))
    return TestClient(app)


def test_metadata_names_the_resource_and_the_identity_provider():
    response = make_client().get("/.well-known/oauth-protected-resource")

    assert response.status_code == 200
    assert response.json() == {
        "resource": PUBLIC_URL,
        "authorization_servers": [ISSUER],
        "bearer_methods_supported": ["header"],
    }


def test_metadata_is_also_served_under_the_resource_path():
    client = make_client()

    plain = client.get("/.well-known/oauth-protected-resource")
    with_path = client.get("/.well-known/oauth-protected-resource/mcp")

    assert with_path.status_code == 200
    assert with_path.json() == plain.json()


def test_metadata_url_follows_the_resource_path():
    assert (
        metadata_url("https://mcp.example.com/mcp")
        == "https://mcp.example.com/.well-known/oauth-protected-resource/mcp"
    )
