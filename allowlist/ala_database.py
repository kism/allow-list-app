"""Handles the Databse of the app."""

import csv
import os

from . import ala_logger

logger = ala_logger.get_logger()


CSV_SCHEMA = {"username": "", "ip": "", "date": ""}


def db_get_allowlist() -> list:
    """Get the allowlist as a dict."""
    allowlist = []

    logger.debug("Building allowlist list from file...")
    try:
        with open(database_path, newline="") as csvfile:
            csv_reader = csv.DictReader(csvfile, quoting=csv.QUOTE_MINIMAL)
            allowlist = list(csv_reader)
    except FileNotFoundError:
        pass
    return allowlist


def db_write_allowlist(allowlist: list) -> True:
    """Insert an IP into the allowlist, returns if an IP has been inserted."""
    with open(database_path, "w", newline="") as csvfile:
        csv_writer = csv.DictWriter(
            csvfile,
            CSV_SCHEMA.keys(),
            delimiter=",",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
        )
        csv_writer.writeheader()
        for item in allowlist:
            csv_writer.writerow(item)


def db_check() -> True:
    """Check the 'schema' of the database."""
    logger.info("Checking Database")
    try:
        with open(database_path, newline="") as csvfile:
            csv_reader = csv.reader(csvfile, quoting=csv.QUOTE_MINIMAL)
            for i, row in enumerate(csv_reader):
                if len(row) != len(CSV_SCHEMA.keys()):
                    err = f"Row {i + 1} of csv not three columns, fix or delete {database_path}"
                    raise ValueError(err)
        logger.info("Database checks passed")
    except FileNotFoundError:
        logger.info("Database file not found, that's okay")


def db_reset() -> None:
    """Clear the database."""
    logger.info("CLEARING THE DATABASE...")
    with open(database_path, "w", newline="") as csvfile:
        csv_writer = csv.DictWriter(csvfile, CSV_SCHEMA.keys(), delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writeheader()


database_path = os.getcwd() + os.sep + "database.csv"
