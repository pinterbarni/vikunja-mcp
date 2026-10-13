"""Logging setup using the std lib, with key/value output for easy grepping."""

import logging

_FORMAT = "%(asctime)s level=%(levelname)s logger=%(name)s msg=%(message)s"


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(format=_FORMAT)
    logging.getLogger().setLevel(level)
