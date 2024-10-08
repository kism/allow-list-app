"""Handles the database of the app."""

import csv
import logging

from flask import current_app

logger = logging.getLogger(__name__)


CSV_SCHEMA = {"username": "", "ip": "", "date": ""}

database_path: str | None = None


def start_database() -> None:
    """Start this module."""
    global database_path  # noqa: PLW0603 Needed due to how flask loads modules.
    database_path = current_app.config["app"]["db_path"]
    db_check()


def db_get_allowlist() -> list:
    """Get the allowlist as a dict."""
    assert database_path is not None  # noqa: S101 Appease mypy, this module should be an object
    allowlist = []

    logger.debug("Building allowlist list from file...")
    try:
        with open(database_path, newline="") as csv_file:
            csv_reader = csv.DictReader(csv_file, quoting=csv.QUOTE_MINIMAL)
            allowlist = list(csv_reader)
    except FileNotFoundError:
        logger.warning("No database found, will be created the first time a IP is added.")
    return allowlist


def db_write_allowlist(allowlist: list) -> None:
    """Insert an IP into the allowlist, returns if an IP has been inserted."""
    assert database_path is not None  # noqa: S101 Appease mypy, this module should be an object
    with open(database_path, "w", newline="") as csv_file:
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
    assert database_path is not None  # noqa: S101 Appease mypy, this module should be an object
    try:
        with open(database_path, newline="") as csv_file:
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
    assert database_path is not None  # noqa: S101 Appease mypy, this module should be an object
    logger.info("CLEARING THE DATABASE...")
    with open(database_path, "w", newline="") as csv_file:
        csv_writer = csv.DictWriter(
            csv_file, CSV_SCHEMA.keys(), delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        csv_writer.writeheader()


logger.debug("Loaded module: %s", __name__)
