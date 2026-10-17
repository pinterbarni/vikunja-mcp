"""What the task tools return."""

from datetime import datetime

from pydantic import BaseModel


class TaskSummary(BaseModel):
    id: int
    title: str
    done: bool
    priority: int
    project_id: int
    due_date: datetime | None


class TaskDetail(BaseModel):
    id: int
    title: str
    description: str
    done: bool
    priority: int
    percent_done: float
    project_id: int
    due_date: datetime | None
    start_date: datetime | None
    end_date: datetime | None
    created: datetime | None
    updated: datetime | None
    labels: list[str]
    assignees: list[str]
