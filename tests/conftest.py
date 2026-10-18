import pytest

from vikunja_mcp.config import Settings, get_settings


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch, tmp_path):
    """Every test starts without settings from the real environment or a local .env file."""
    for name in Settings.model_fields:
        monkeypatch.delenv(name.upper(), raising=False)
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def settings() -> Settings:
    """Settings that never read the real environment or a local .env file."""
    return Settings(
        _env_file=None,
        vikunja_url="https://vikunja.test.url",
        vikunja_api_token="example-test-token",
        allowed_hosts=["testserver"],
    )
