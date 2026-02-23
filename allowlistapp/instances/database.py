"""Database singleton instance."""

import logging

from allowlistapp.services.database import Database

logger = logging.getLogger(__name__)

_database: Database | None = None


def get_database() -> Database:
    """Get the Database singleton instance."""
    global _database  # noqa: PLW0603
    if _database is None:
        _database = Database()
    return _database


logger.debug("Loaded module: %s", __name__)
