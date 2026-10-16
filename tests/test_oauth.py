import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from vikunja_mcp.oauth import InvalidToken, TokenVerifier

ISSUER = "https://example.authkit.app"
AUDIENCE = "https://mcp.example.com/mcp"


@pytest.fixture(scope="module")
def private_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope="module")
def other_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def verifier(private_key):
    public_key = private_key.public_key()
    return TokenVerifier(
        issuer=ISSUER,
        audience=AUDIENCE,
        resolve_key=lambda token: public_key,
    )


def make_token(key, drop=(), **overrides):
    now = int(time.time())
    claims = {"iss": ISSUER, "aud": AUDIENCE, "sub": "user_01ABC", "iat": now, "exp": now + 300}
    claims.update(overrides)
    for name in drop:
        del claims[name]
    return jwt.encode(claims, key, algorithm="RS256")


def test_valid_token_returns_its_claims(verifier, private_key):
    claims = verifier.verify(make_token(private_key))

    assert claims["sub"] == "user_01ABC"


def test_expired_token_is_rejected(verifier, private_key):
    token = make_token(private_key, exp=int(time.time()) - 60)

    with pytest.raises(InvalidToken):
        verifier.verify(token)


def test_token_for_another_audience_is_rejected(verifier, private_key):
    token = make_token(private_key, aud="https://other.example.com/mcp")

    with pytest.raises(InvalidToken):
        verifier.verify(token)


def test_token_from_another_issuer_is_rejected(verifier, private_key):
    token = make_token(private_key, iss="https://evil.example.com")

    with pytest.raises(InvalidToken):
        verifier.verify(token)


def test_token_signed_with_another_key_is_rejected(verifier, other_key):
    with pytest.raises(InvalidToken):
        verifier.verify(make_token(other_key))


def test_token_without_subject_is_rejected(verifier, private_key):
    with pytest.raises(InvalidToken):
        verifier.verify(make_token(private_key, drop=("sub",)))


def test_token_with_a_symmetric_algorithm_is_rejected(verifier):
    now = int(time.time())
    claims = {"iss": ISSUER, "aud": AUDIENCE, "sub": "user_01ABC", "exp": now + 300}
    token = jwt.encode(claims, "a-shared-secret-of-enough-length-1234", algorithm="HS256")

    with pytest.raises(InvalidToken):
        verifier.verify(token)


def test_garbage_is_rejected(verifier):
    with pytest.raises(InvalidToken):
        verifier.verify("not-a-jwt")


def test_key_lookup_failure_is_rejected(private_key):
    def unknown_key(token):
        raise jwt.PyJWKClientError("no key with this kid")

    verifier = TokenVerifier(issuer=ISSUER, audience=AUDIENCE, resolve_key=unknown_key)

    with pytest.raises(InvalidToken):
        verifier.verify(make_token(private_key))
