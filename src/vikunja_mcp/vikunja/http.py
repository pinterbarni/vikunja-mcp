"""Low-level HTTP access to Vikunja: one request method and the error mapping."""

from typing import Any

import httpx

from vikunja_mcp.vikunja.errors import VikunjaAPIError, VikunjaUnreachable


class VikunjaHttp:
    """Sends requests to Vikunja and turns failures into Vikunja errors."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        try:
            response = await self._client.request(method, path, params=params, json=json)
        except httpx.HTTPError as exc:
            raise VikunjaUnreachable(f"Could not reach Vikunja: {exc}") from exc
        if response.is_error:
            raise VikunjaAPIError(response.status_code, _error_message(response))
        return response.json()

    async def aclose(self) -> None:
        await self._client.aclose()


def _error_message(response: httpx.Response) -> str:
    try:
        return str(response.json().get("message", response.text))
    except ValueError:
        return response.text
