"""Slices of the Vikunja API responses that this server cares about.

Unknown fields are ignored, so newer Vikunja versions do not break parsing.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    title: str
    description: str = ""
    is_archived: bool = False
    parent_project_id: int = 0


class Task(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    title: str
    description: str = ""
    done: bool = False
    priority: int = 0
    project_id: int = 0
    due_date: datetime | None = None

    @field_validator("due_date")
    @classmethod
    def _zero_date_means_none(cls, value: datetime | None) -> datetime | None:
        """0001-01-01 for 'no due date'"""
        if value is not None and value.year <= 1:
            return None
        return value


class ServerInfo(BaseModel):
    """Vikunja's public info endpoint's info"""

    model_config = ConfigDict(extra="ignore")

    version: str
