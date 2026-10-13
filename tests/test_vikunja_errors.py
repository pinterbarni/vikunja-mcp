import pytest

from vikunja_mcp.vikunja.errors import VikunjaAPIError, VikunjaError, VikunjaUnreachable


def test_api_error_keeps_status_and_message() -> None:
    error = VikunjaAPIError(401, "invalid token")

    assert error.status_code == 401
    assert error.message == "invalid token"
    assert str(error) == "Vikunja returned 401: invalid token"


@pytest.mark.parametrize("error_type", [VikunjaUnreachable, VikunjaAPIError])
def test_all_errors_share_one_base_class(error_type: type[VikunjaError]) -> None:
    assert issubclass(error_type, VikunjaError)


def test_one_except_clause_catches_both() -> None:
    caught = []
    for error in (VikunjaUnreachable("down"), VikunjaAPIError(500, "boom")):
        try:
            raise error
        except VikunjaError as exc:
            caught.append(exc)

    assert len(caught) == 2
