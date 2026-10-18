import pytest
from mcp.server.mcpserver.exceptions import ToolError

from vikunja_mcp.tools.errors import friendly_errors
from vikunja_mcp.vikunja.errors import VikunjaAPIError, VikunjaUnreachable


def failing(error: Exception):
    @friendly_errors
    async def tool() -> None:
        raise error

    return tool


async def test_good_results_pass_through() -> None:
    @friendly_errors
    async def tool() -> int:
        return 42

    assert await tool() == 42


async def test_unreachable_becomes_a_readable_message() -> None:
    with pytest.raises(ToolError, match="Could not reach Vikunja"):
        await failing(VikunjaUnreachable("boom"))()


async def test_not_found_keeps_the_reason() -> None:
    with pytest.raises(ToolError, match="Not found.*does not exist"):
        await failing(VikunjaAPIError(404, "The task does not exist."))()


async def test_a_rejected_token_points_at_the_setting() -> None:
    with pytest.raises(ToolError, match="VIKUNJA_API_TOKEN"):
        await failing(VikunjaAPIError(401, "invalid token"))()


async def test_other_api_errors_keep_status_and_message() -> None:
    with pytest.raises(ToolError, match="500.*database down"):
        await failing(VikunjaAPIError(500, "database down"))()
