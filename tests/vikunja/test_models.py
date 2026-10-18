from datetime import UTC, datetime

from vikunja_mcp.vikunja.models import Project, ServerInfo, Task


def test_project_parses_a_vikunja_payload() -> None:
    payload = {
        "id": 7,
        "title": "Home",
        "description": "House stuff",
        "is_archived": True,
        "parent_project_id": 3,
    }

    project = Project.model_validate(payload)

    assert project.id == 7
    assert project.title == "Home"
    assert project.description == "House stuff"
    assert project.is_archived is True
    assert project.parent_project_id == 3


def test_project_ignores_fields_it_does_not_know() -> None:
    payload = {"id": 1, "title": "Inbox", "owner": {"id": 9}, "hex_color": "ff0000"}

    project = Project.model_validate(payload)

    assert project.id == 1
    assert not hasattr(project, "owner")


def test_project_optional_fields_have_defaults() -> None:
    project = Project.model_validate({"id": 1, "title": "Inbox"})

    assert project.description == ""
    assert project.is_archived is False
    assert project.parent_project_id == 0


def test_server_info_reads_version_and_ignores_the_rest() -> None:
    info = ServerInfo.model_validate(
        {"version": "v2.7.0", "motd": "", "auth": {"local": {"enabled": True}}}
    )

    assert info.version == "v2.7.0"
    # todo: change later, now it's baked in as other examples.. has a counterpart in client


def test_task_reads_known_fields_and_ignores_the_rest() -> None:
    task = Task.model_validate(
        {
            "id": 7,
            "title": "Call the bank",
            "done": True,
            "priority": 3,
            "project_id": 1,
            "labels": [{"id": 1, "title": "home"}],
            "created_by": {"id": 1},
        }
    )

    assert (task.id, task.title, task.done, task.priority, task.project_id) == (
        7,
        "Call the bank",
        True,
        3,
        1,
    )


def test_task_zero_due_date_means_no_due_date() -> None:
    task = Task.model_validate({"id": 1, "title": "x", "due_date": "0001-01-01T00:00:00Z"})

    assert task.due_date is None


def test_task_keeps_a_real_due_date() -> None:
    task = Task.model_validate({"id": 1, "title": "x", "due_date": "2026-10-20T10:00:00Z"})

    assert task.due_date == datetime(2026, 10, 20, 10, 0, tzinfo=UTC)


def test_task_reads_labels_assignees_progress_and_dates() -> None:
    task = Task.model_validate(
        {
            "id": 1,
            "title": "x",
            "labels": [{"id": 3, "title": "urgent", "hex_color": "ff0000"}],
            "assignees": [{"id": 1, "username": "testuser", "name": ""}],
            "percent_done": 0.5,
            "start_date": "0001-01-01T00:00:00Z",
            "end_date": "2026-10-25T10:00:00Z",
            "created": "2026-10-13T20:49:17Z",
        }
    )

    assert [label.title for label in task.labels] == ["urgent"]
    assert [a.username for a in task.assignees] == ["testuser"]
    assert task.percent_done == 0.5
    assert task.start_date is None
    assert task.end_date == datetime(2026, 10, 25, 10, 0, tzinfo=UTC)
    assert task.created is not None


def test_task_null_labels_and_assignees_become_empty_lists() -> None:
    task = Task.model_validate({"id": 1, "title": "x", "labels": None, "assignees": None})

    assert task.labels == []
    assert task.assignees == []
