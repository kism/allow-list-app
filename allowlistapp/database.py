"""Handles the database of the app."""

import csv
import logging
from pathlib import Path
from typing import Any

from flask import current_app

logger = logging.getLogger(__name__)


CSV_SCHEMA = {"username": "", "ip": "", "date": ""}

_database_path: Path | None = None


def get_database_path() -> Path:
    """Get the path to the database."""
    if _database_path is None:
        msg = "Database path not set, did you call start_database()?"
        raise ValueError(msg)
    return _database_path


def start_database() -> None:
    """Start this module."""
    global _database_path  # noqa: PLW0603 Needed due to how flask loads modules.
    _database_path = current_app.config.app.db_path
    db_check()


def db_get_allowlist() -> list[dict[str, Any]]:
    """Get the allowlist as a dict."""
    database_path = get_database_path()
    allowlist = []

    logger.debug("Building allowlist list from file...")
    try:
        with database_path.open(newline="") as csv_file:
            csv_reader = csv.DictReader(csv_file, quoting=csv.QUOTE_MINIMAL)
            allowlist = list(csv_reader)
    except FileNotFoundError:
        logger.warning("No database found, will be created the first time a IP is added.")
    return allowlist


def db_write_allowlist(allowlist: list[dict[str, Any]]) -> None:
    """Insert an IP into the allowlist, returns if an IP has been inserted."""
    database_path = get_database_path()

    with database_path.open("w", newline="") as csv_file:
        csv_writer = csv.DictWriter(
            csv_file,
            CSV_SCHEMA.keys(),
            delimiter=",",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
        )
        csv_writer.writeheader()
        for item in allowlist:
            csv_writer.writerow(item)

    logger.info("DB write complete.")


def db_check() -> None:
    """Check the 'schema' of the database."""
    database_path = get_database_path()
    try:
        with database_path.open(newline="") as csv_file:
            msg = f"Database found at: {database_path}"
            logger.info(msg)
            csv_reader = csv.DictReader(csv_file, quoting=csv.QUOTE_MINIMAL)
            allowlist = list(csv_reader).copy()

        msg = f"CSV DictReader as list:\n{allowlist}"
        logger.debug(msg)

        for row in allowlist:
            if len(row) != len(CSV_SCHEMA.keys()):
                err = f"Row {row} of csv not three columns, fix or delete {database_path}"
                logger.critical(err)
                raise ValueError(err)
        logger.info("Database checks passed")
    except FileNotFoundError:
        logger.info("Database file not found, that's okay")


def db_reset() -> None:
    """Clear the database."""
    database_path = get_database_path()
    logger.info("CLEARING THE DATABASE...")
    with database_path.open("w", newline="") as csv_file:
        csv_writer = csv.DictWriter(
            csv_file, CSV_SCHEMA.keys(), delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        csv_writer.writeheader()


logger.debug("Loaded module: %s", __name__)
