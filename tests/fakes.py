"""In-memory stubs for Vikunja, used by tests instead of the network."""

from vikunja_mcp.vikunja.models import Project, ServerInfo


class FakeVikunjaClient:
    def __init__(
        self,
        projects: list[Project] | None = None,
        version: str = "v0.0.0-fake",
        error: Exception | None = None,
    ) -> None:
        self.projects = projects or []
        self.version = version
        self.error = error
        self.closed = False

    async def get_info(self) -> ServerInfo:
        self._fail_if_told_to()
        return ServerInfo(version=self.version)

    async def list_projects(self, include_archived: bool = False) -> list[Project]:
        self._fail_if_told_to()
        return [p for p in self.projects if include_archived or not p.is_archived]

    async def aclose(self) -> None:
        self.closed = True

    def _fail_if_told_to(self) -> None:
        if self.error is not None:
            raise self.error
