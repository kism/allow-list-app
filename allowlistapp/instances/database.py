"""Database singleton instance."""

import logging

from allowlistapp.services.database import Database

logger = logging.getLogger(__name__)

_database: Database | None = None


def get_database() -> Database:
    """Get the Database singleton instance."""
    if _database is None:
        msg = "Database not initialized, call init_database() first"
        raise ValueError(msg)
    return _database


def init_database() -> None:
    """Initialize the Database singleton."""
    global _database  # noqa: PLW0603
    _database = Database()


logger.debug("Loaded module: %s", __name__)
