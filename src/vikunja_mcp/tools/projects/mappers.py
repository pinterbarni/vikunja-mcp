"""Turn Vikunja projects into the models the project tools return."""

from vikunja_mcp.tools.projects.models import ProjectSummary
from vikunja_mcp.vikunja.models import Project


def to_summary(project: Project) -> ProjectSummary:
    return ProjectSummary(id=project.id, title=project.title, archived=project.is_archived)
