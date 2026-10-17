"""Public metadata that tells OAuth clients how to log in to this server."""

from urllib.parse import urlparse

from fastapi import APIRouter

_PREFIX = "/.well-known/oauth-protected-resource"


def metadata_url(public_url: str) -> str:
    """Where clients find the metadata of this resource (RFC 9728, path variant)."""
    parts = urlparse(public_url)
    return f"{parts.scheme}://{parts.netloc}{_PREFIX}{parts.path.rstrip('/')}"


def build_router(*, public_url: str, issuer: str) -> APIRouter:
    """Serve RFC 9728 protected resource metadata at the plain and the path variant."""
    document = {
        "resource": public_url,
        "authorization_servers": [issuer],
        "bearer_methods_supported": ["header"],
    }

    def metadata() -> dict[str, object]:
        return document

    router = APIRouter()
    paths = [_PREFIX]
    resource_path = urlparse(public_url).path.rstrip("/")
    if resource_path:
        paths.append(f"{_PREFIX}{resource_path}")
    for path in paths:
        router.add_api_route(path, metadata, methods=["GET"])
    return router
