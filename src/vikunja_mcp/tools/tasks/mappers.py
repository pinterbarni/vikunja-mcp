"""Turn Vikunja tasks into the models the task tools return."""

from vikunja_mcp.tools.tasks.models import TaskDetail, TaskSummary
from vikunja_mcp.vikunja.models import Task


def to_summary(task: Task) -> TaskSummary:
    return TaskSummary(
        id=task.id,
        title=task.title,
        done=task.done,
        priority=task.priority,
        project_id=task.project_id,
        due_date=task.due_date,
    )


def to_detail(task: Task) -> TaskDetail:
    return TaskDetail(
        id=task.id,
        title=task.title,
        description=task.description,
        done=task.done,
        priority=task.priority,
        percent_done=task.percent_done,
        project_id=task.project_id,
        due_date=task.due_date,
        start_date=task.start_date,
        end_date=task.end_date,
        created=task.created,
        updated=task.updated,
        labels=[label.title for label in task.labels],
        assignees=[a.username for a in task.assignees],
    )
