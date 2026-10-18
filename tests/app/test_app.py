from fastapi.testclient import TestClient

from tests.fakes import FakeVikunjaClient
from vikunja_mcp.config import Settings
from vikunja_mcp.main import create_app


def test_create_app_keeps_the_injected_client(settings: Settings) -> None:
    fake = FakeVikunjaClient()

    app = create_app(settings, client=fake)

    assert app.state.vikunja is fake


def test_create_app_closes_the_client_on_shutdown(settings: Settings) -> None:
    fake = FakeVikunjaClient()

    with TestClient(create_app(settings, client=fake)):
        assert not fake.closed

    assert fake.closed
