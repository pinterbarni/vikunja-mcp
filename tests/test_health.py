from fastapi.testclient import TestClient

from tests.fakes import FakeVikunjaClient
from vikunja_mcp import __version__
from vikunja_mcp.config import Settings
from vikunja_mcp.main import create_app
from vikunja_mcp.vikunja.errors import VikunjaUnreachable


def test_health_reports_the_vikunja_version_when_reachable(settings: Settings) -> None:
    fake = FakeVikunjaClient(version="v2.7.0")

    with TestClient(create_app(settings, client=fake)) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "version": __version__,
        "vikunja_reachable": True,
        "vikunja_version": "v2.7.0",
    }


def test_health_is_degraded_but_still_200_when_vikunja_is_down(settings: Settings) -> None:
    fake = FakeVikunjaClient(error=VikunjaUnreachable("down"))

    with TestClient(create_app(settings, client=fake)) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "degraded",
        "version": __version__,
        "vikunja_reachable": False,
        "vikunja_version": None,
    }
