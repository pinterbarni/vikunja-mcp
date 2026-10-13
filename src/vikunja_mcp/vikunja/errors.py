"""Errors raised by the Vikunja client."""


class VikunjaError(Exception):
    """Base class for everything that goes wrong talking to Vikunja."""


class VikunjaUnreachable(VikunjaError):
    """Vikunja could not be reached (network error or timeout)."""


class VikunjaAPIError(VikunjaError):
    """Vikunja answered with an error status."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"Vikunja returned {status_code}: {message}")
        self.status_code = status_code
        self.message = message
