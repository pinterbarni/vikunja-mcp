"""Slices of the Vikunja API responses that this server cares about.

Unknown fields are ignored, so newer Vikunja versions do not break parsing.
"""

from pydantic import BaseModel, ConfigDict


class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    title: str
    description: str = ""
    is_archived: bool = False
    parent_project_id: int = 0
