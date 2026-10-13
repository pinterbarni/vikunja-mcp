from fastapi.testclient import TestClient

from vikunja_mcp import __version__
from vikunja_mcp.config import Settings
from vikunja_mcp.main import create_app


def test_health_reports_ok(settings: Settings) -> None:
    client = TestClient(create_app(settings))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__}
