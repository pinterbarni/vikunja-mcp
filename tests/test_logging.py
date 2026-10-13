import logging

from vikunja_mcp.config import Settings
from vikunja_mcp.logging_config import configure_logging
from vikunja_mcp.main import create_app


def test_configure_logging_sets_root_level() -> None:
    root = logging.getLogger()
    original = root.level
    try:
        configure_logging("WARNING")
        assert root.level == logging.WARNING
    finally:
        root.setLevel(original)


def test_app_logs_a_startup_line(settings: Settings, caplog) -> None:
    with caplog.at_level(logging.INFO, logger="vikunja_mcp.main"):
        create_app(settings)

    assert "starting" in caplog.text
    assert "https://vikunja.test" in caplog.text
    assert "test-token" not in caplog.text
