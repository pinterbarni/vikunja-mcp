"""Application settings, read from environment variables."""

from functools import lru_cache
from typing import Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from vikunja_mcp.constants import (
    API_SUFFIX,
    DEFAULT_LOG_LEVEL,
    DEFAULT_TIMEOUT_SECONDS,
    ENV_FILE,
    ENV_FILE_ENCODING,
    LOCAL_HOSTS,
    LOG_LEVELS,
)


class Settings(BaseSettings):
    """Configuration for the server, read from environment variables or a local .env file."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE, env_file_encoding=ENV_FILE_ENCODING, extra="ignore"
    )

    vikunja_url: str
    vikunja_api_token: SecretStr
    vikunja_timeout_seconds: float = Field(default=DEFAULT_TIMEOUT_SECONDS, gt=0)
    log_level: str = DEFAULT_LOG_LEVEL
    allowed_hosts: list[str] = Field(
        default_factory=lambda: list(LOCAL_HOSTS),
        description="Host headers accepted on /mcp (DNS rebinding protection). "
        "Add your public domain, for example mcp.example.com. JSON list in the environment.",
    )
    mcp_auth_token: SecretStr | None = None
    oauth_issuer: str | None = None
    public_url: str | None = None
    oauth_allowed_subjects: list[str] = []

    @field_validator("mcp_auth_token")
    @classmethod
    def _blank_token_means_no_auth(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None and not value.get_secret_value().strip():
            return None
        return value

    @field_validator("oauth_issuer", "public_url", mode="before")
    @classmethod
    def _blank_to_none(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip()

    @field_validator("oauth_issuer")
    @classmethod
    def _strip_trailing_slash(cls, value: str | None) -> str | None:
        return value.rstrip("/") if value else value

    @model_validator(mode="after")
    def _oauth_needs_public_url(self) -> Self:
        if self.oauth_issuer and not self.public_url:
            raise ValueError("PUBLIC_URL is required when OAUTH_ISSUER is set")
        return self

    @field_validator("vikunja_url")
    @classmethod
    def _normalise_url(cls, value: str) -> str:
        """Accept the URL with or without a trailing slash or the /api/v1 suffix."""
        value = value.strip().rstrip("/")
        if value.endswith(API_SUFFIX):
            value = value.removesuffix(API_SUFFIX)
        if not value.startswith(("http://", "https://")):
            raise ValueError("must start with http:// or https://")
        return value

    @field_validator("log_level")
    @classmethod
    def _normalise_log_level(cls, value: str) -> str:
        """Accept any casing, reject names that are not real log levels."""
        value = value.strip().upper()
        if value not in LOG_LEVELS:
            raise ValueError(f"must be one of {sorted(LOG_LEVELS)}")
        return value

    @property
    def vikunja_api_base_url(self) -> str:
        return f"{self.vikunja_url}{API_SUFFIX}"


@lru_cache
def get_settings() -> Settings:
    """Load settings once and reuse them."""
    return Settings()
