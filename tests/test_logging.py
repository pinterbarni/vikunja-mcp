import logging

from vikunja_mcp.logging_config import configure_logging


def test_configure_logging_sets_root_level() -> None:
    root = logging.getLogger()
    original = root.level
    try:
        configure_logging("WARNING")
        assert root.level == logging.WARNING
    finally:
        root.setLevel(original)
