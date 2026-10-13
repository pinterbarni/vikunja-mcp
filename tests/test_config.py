import pytest
from pydantic import ValidationError

from vikunja_mcp.config import Settings


def test_reads_values_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VIKUNJA_URL", "https://vikunja.example.com")
    monkeypatch.setenv("VIKUNJA_API_TOKEN", "secret-token")

    settings = Settings(_env_file=None)  # don't read from real env file please!!! :D

    assert settings.vikunja_url == "https://vikunja.example.com"
    assert settings.vikunja_api_token == "secret-token"


def test_token_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VIKUNJA_API_TOKEN", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None, vikunja_url="https://vikunja.example.com")
