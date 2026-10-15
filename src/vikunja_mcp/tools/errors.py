"""Turn Vikunja errors into short messages that LLMs can read and act on."""

import functools
from collections.abc import Awaitable, Callable

from mcp.server.mcpserver.exceptions import ToolError

from vikunja_mcp.vikunja.errors import VikunjaAPIError, VikunjaError, VikunjaUnreachable


def to_message(error: VikunjaError) -> str:
    if isinstance(error, VikunjaUnreachable):
        return "Could not reach Vikunja. Check that it is running, then try again."
    if isinstance(error, VikunjaAPIError):
        if error.status_code == 404:
            return f"Not found: {error}"
        if error.status_code in (401, 403):
            return "Vikunja rejected the API token. Check VIKUNJA_API_TOKEN and its permissions."
        return f"Vikunja returned an error ({error.status_code}): {error}"
    return str(error)


def friendly_errors[**P, R](tool: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    """Wrap a tool so Vikunja errors reach LLMs as a clear ToolError message."""

    @functools.wraps(tool)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return await tool(*args, **kwargs)
        except VikunjaError as exc:
            raise ToolError(to_message(exc)) from exc

    return wrapper
