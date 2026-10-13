import pytest

from vikunja_mcp.config import Settings


@pytest.fixture
def settings() -> Settings:
    """Settings that never read the real environment or a local .env file."""
    return Settings(
        _env_file=None,
        vikunja_url="https://vikunja.test.url",
        vikunja_api_token="example-test-token",
    )
