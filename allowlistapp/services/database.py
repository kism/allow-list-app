"""Database service for the allowlist."""

import csv
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

CSV_SCHEMA = {"username": "", "ip": "", "date": ""}


class Database:
    """Manages the CSV allowlist database."""

    def __init__(self, db_path: Path | None) -> None:
        """Initialise the database, verifying it exists and has the correct schema."""
        if db_path is None:
            msg = "db_path not configured"
            raise ValueError(msg)
        self.db_path = db_path
        self._check()

    def get_allowlist(self) -> list[dict[str, Any]]:
        """Get the allowlist as a list of dicts."""
        allowlist = []

        logger.debug("Building allowlist list from file...")
        try:
            with self.db_path.open(newline="") as csv_file:
                csv_reader = csv.DictReader(csv_file, quoting=csv.QUOTE_MINIMAL)
                allowlist = list(csv_reader)
        except FileNotFoundError:
            logger.warning("No database found, will be created the first time a IP is added.")
        return allowlist

    def write_allowlist(self, allowlist: list[dict[str, Any]]) -> None:
        """Write the allowlist to the database."""
        with self.db_path.open("w", newline="") as csv_file:
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

    def reset(self) -> None:
        """Clear the database."""
        logger.info("CLEARING THE DATABASE...")
        with self.db_path.open("w", newline="") as csv_file:
            csv_writer = csv.DictWriter(
                csv_file, CSV_SCHEMA.keys(), delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
            )
            csv_writer.writeheader()

    def _check(self) -> None:
        """Check the 'schema' of the database."""
        try:
            with self.db_path.open(newline="") as csv_file:
                msg = f"Database found at: {self.db_path}"
                logger.info(msg)
                csv_reader = csv.DictReader(csv_file, quoting=csv.QUOTE_MINIMAL)
                allowlist = list(csv_reader).copy()

            msg = f"CSV DictReader as list:\n{allowlist}"
            logger.debug(msg)

            for row in allowlist:
                if len(row) != len(CSV_SCHEMA.keys()):
                    err = f"Row {row} of csv not three columns, fix or delete {self.db_path}"
                    logger.critical(err)
                    raise ValueError(err)
            logger.info("Database checks passed")
        except FileNotFoundError:
            logger.info("Database file not found, that's okay")


logger.debug("Loaded module: %s", __name__)
