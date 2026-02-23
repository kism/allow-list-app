"""Database singleton instance."""

import logging
from pathlib import Path

from allowlistapp.instances.config import get_ala_config
from allowlistapp.services.database import Database

logger = logging.getLogger(__name__)

_database: Database | None = None
_database_path: Path | None = None


def get_database() -> Database:
    """Get the Database singleton instance."""
    global _database  # noqa: PLW0603
    global _database_path  # noqa: PLW0603

    db_path = get_ala_config().app.db_path
    if db_path is None:
        msg = "db_path not configured"
        raise ValueError(msg)

    if _database is None or _database_path != db_path:
        _database = Database()
        _database_path = db_path
    return _database


logger.debug("Loaded module: %s", __name__)
