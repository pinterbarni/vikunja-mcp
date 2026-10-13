"""Application settings, read from environment variables."""

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_API_SUFFIX = "/api/v1"


class Settings(BaseSettings):
    """Configuration for the server, read from environment variables or a local .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    vikunja_url: str
    vikunja_api_token: SecretStr

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

    @property
    def vikunja_api_base_url(self) -> str:
        return f"{self.vikunja_url}{_API_SUFFIX}"
