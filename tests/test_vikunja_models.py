from vikunja_mcp.vikunja.models import Project


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
