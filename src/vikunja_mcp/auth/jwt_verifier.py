"""Check OAuth access tokens (JWT) issued by the identity provider."""

from collections.abc import Callable
from typing import Any

import jwt

KeyResolver = Callable[[str], Any]


class InvalidToken(Exception):
    """The token is missing, malformed, expired or not meant for this server."""


class TokenVerifier:
    def __init__(self, *, issuer: str, audience: str, resolve_key: KeyResolver) -> None:
        self._issuer = issuer
        self._audience = audience
        self._resolve_key = resolve_key

    def verify(self, token: str) -> dict[str, Any]:
        """Return the claims of a valid token, or raise InvalidToken."""
        try:
            key = self._resolve_key(token)
            return jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                issuer=self._issuer,
                audience=self._audience,
                options={"require": ["exp", "iss", "aud", "sub"]},
            )
        except jwt.PyJWTError as error:
            raise InvalidToken(str(error)) from error


def jwks_key_resolver(issuer: str) -> KeyResolver:
    """Look up signing keys on the provider. The client caches the key list."""
    client = jwt.PyJWKClient(f"{issuer}/oauth2/jwks")

    def resolve(token: str) -> Any:
        return client.get_signing_key_from_jwt(token).key

    return resolve
