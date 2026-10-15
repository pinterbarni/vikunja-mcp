"""Slices of the Vikunja API responses that this server cares about.

Unknown fields are ignored, so newer Vikunja versions do not break parsing.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    title: str
    description: str = ""
    is_archived: bool = False
    parent_project_id: int = 0


class Label(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    title: str


class Assignee(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    username: str
    name: str = ""


class Task(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    title: str
    description: str = ""
    done: bool = False
    priority: int = 0
    project_id: int = 0
    percent_done: float = 0.0
    due_date: datetime | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    created: datetime | None = None
    updated: datetime | None = None
    labels: list[Label] = Field(default_factory=list)
    assignees: list[Assignee] = Field(default_factory=list)

    @field_validator("labels", "assignees", mode="before")
    @classmethod
    def _null_means_empty(cls, value: object) -> object:
        """Vikunja sends null instead of an empty list."""
        return [] if value is None else value

    @field_validator("due_date", "start_date", "end_date")
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
