"""Application settings, read from environment variables."""

from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_API_SUFFIX = "/api/v1"
_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
_LOCAL_HOSTS = ["localhost:*", "127.0.0.1:*"]


class Settings(BaseSettings):
    """Configuration for the server, read from environment variables or a local .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    vikunja_url: str
    vikunja_api_token: SecretStr
    vikunja_timeout_seconds: float = Field(default=10.0, gt=0)
    log_level: str = "INFO"
    allowed_hosts: list[str] = Field(
        default_factory=lambda: list(_LOCAL_HOSTS),
        description="Host headers accepted on /mcp (DNS rebinding protection). "
        "Add your public domain, for example mcp.example.com. JSON list in the environment.",
    )
    mcp_auth_token: SecretStr | None = None

    @field_validator("mcp_auth_token")
    @classmethod
    def _blank_token_means_no_auth(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None and not value.get_secret_value().strip():
            return None
        return value

    @field_validator("vikunja_url")
    @classmethod
    def _normalise_url(cls, value: str) -> str:
        """Accept the URL with or without a trailing slash or the /api/v1 suffix."""
        value = value.strip().rstrip("/")
        if value.endswith(_API_SUFFIX):
            value = value.removesuffix(_API_SUFFIX)
        if not value.startswith(("http://", "https://")):
            raise ValueError("must start with http:// or https://")
        return value

    @field_validator("log_level")
    @classmethod
    def _normalise_log_level(cls, value: str) -> str:
        """Accept any casing of value, reject names that are not real log levels defined by us."""
        value = value.strip().upper()
        if value not in _LOG_LEVELS:
            raise ValueError(f"must be one of {sorted(_LOG_LEVELS)}")
        return value

    @property
    def vikunja_api_base_url(self) -> str:
        return f"{self.vikunja_url}{_API_SUFFIX}"


@lru_cache
def get_settings() -> Settings:
    """Load settings once and reuse them."""
    return Settings()
