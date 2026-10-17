"""What the project tools return."""

from pydantic import BaseModel


class ProjectSummary(BaseModel):
    id: int
    title: str
    archived: bool
