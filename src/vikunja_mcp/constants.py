"""
Fixed values used across the server.
Values a user can change live in config.py as settings.
"""

# Vikunja API
API_SUFFIX = "/api/v1"
NO_DATE = "0001-01-01T00:00:00Z"
INBOX_PROJECT_NAME = "inbox"

# Settings defaults
ENV_FILE = ".env"
ENV_FILE_ENCODING = "utf-8"
DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_LOG_LEVEL = "INFO"
LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})
LOCAL_HOSTS = ("localhost:*", "127.0.0.1:*")
