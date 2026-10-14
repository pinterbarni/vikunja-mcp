import pytest
from pydantic import ValidationError

from vikunja_mcp.config import Settings


def test_reads_values_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VIKUNJA_URL", "https://vikunja.example.com")
    monkeypatch.setenv("VIKUNJA_API_TOKEN", "secret-token")

    settings = Settings(_env_file=None)  # don't read from real env file please!!! :D

    assert settings.vikunja_url == "https://vikunja.example.com"
    assert settings.vikunja_api_token.get_secret_value() == "secret-token"


def test_token_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VIKUNJA_API_TOKEN", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None, vikunja_url="https://vikunja.example.com")


@pytest.mark.parametrize(
    "raw_url",
    [
        "https://vikunja.example.com",
        "https://vikunja.example.com/",
        "https://vikunja.example.com/api/v1",
        "https://vikunja.example.com/api/v1/",
    ],
)
def test_url_is_normalised(raw_url: str) -> None:
    settings = Settings(_env_file=None, vikunja_url=raw_url, vikunja_api_token="t")

    assert settings.vikunja_url == "https://vikunja.example.com"
    assert settings.vikunja_api_base_url == "https://vikunja.example.com/api/v1"


def test_url_without_scheme_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, vikunja_url="vikunja.example.com", vikunja_api_token="t")


def test_token_does_not_leak_in_repr() -> None:
    settings = Settings(
        _env_file=None,
        vikunja_url="https://vikunja.example.com",
        vikunja_api_token="super-secret",
    )

    assert "super-secret" not in repr(settings)
    assert "super-secret" not in str(settings)


def test_timeout_defaults_to_ten_seconds() -> None:
    settings = Settings(
        _env_file=None,
        vikunja_url="https://vikunja.example.com",
        vikunja_api_token="t",
    )

    assert settings.vikunja_timeout_seconds == 10.0


@pytest.mark.parametrize(
    "bad_timeout", [0.0, -1.0, -5.5], ids=["zero", "negative_integer", "negative_float"]
)
def test_timeout_must_be_positive(bad_timeout: float) -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            vikunja_url="https://vikunja.example.com",
            vikunja_api_token="t",
            vikunja_timeout_seconds=bad_timeout,
        )


def test_log_level_defaults_to_info() -> None:
    settings = Settings(
        _env_file=None,
        vikunja_url="https://vikunja.example.com",
        vikunja_api_token="t",
    )

    assert settings.log_level == "INFO"


def test_log_level_is_case_insensitive() -> None:
    settings = Settings(
        _env_file=None,
        vikunja_url="https://vikunja.example.com",
        vikunja_api_token="t",
        log_level="debug",
    )

    assert settings.log_level == "DEBUG"


def test_unknown_log_level_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            vikunja_url="https://vikunja.example.com",
            vikunja_api_token="t",
            log_level="loud",
        )


def test_allowed_hosts_default_to_local_only(monkeypatch) -> None:
    monkeypatch.setenv("VIKUNJA_URL", "https://vikunja.example.com")
    monkeypatch.setenv("VIKUNJA_API_TOKEN", "token")
    monkeypatch.delenv("ALLOWED_HOSTS", raising=False)

    settings = Settings(_env_file=None)

    assert settings.allowed_hosts == ["localhost:*", "127.0.0.1:*"]


def test_allowed_hosts_are_read_as_a_json_list(monkeypatch) -> None:
    monkeypatch.setenv("VIKUNJA_URL", "https://vikunja.example.com")
    monkeypatch.setenv("VIKUNJA_API_TOKEN", "token")
    monkeypatch.setenv("ALLOWED_HOSTS", '["mcp.example.com"]')

    settings = Settings(_env_file=None)

    assert settings.allowed_hosts == ["mcp.example.com"]
