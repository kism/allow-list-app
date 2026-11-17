"""Database service for the allowlist."""

import csv
from typing import TYPE_CHECKING, Any

from allowlistapp.utils.logger import get_logger

if TYPE_CHECKING:
    from pathlib import Path

logger = get_logger(__name__)

CSV_SCHEMA = {"username": "", "ip": "", "date": ""}


class Database:
    """Manages the CSV allowlist database."""

    def __init__(self, db_path: Path) -> None:
        """Initialise the database, verifying it exists and has the correct schema."""
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

    def _check(self) -> None:
        """Check the 'schema' of the database."""
        if not self.db_path.is_file():
            logger.info("Database file not found, that's okay")
            return

        logger.info("Database found at: %s", self.db_path)
        allowlist = self.get_allowlist()
        logger.debug("CSV DictReader as list:\n%s", allowlist)

        for row in allowlist:
            if len(row) != len(CSV_SCHEMA):
                err = f"Row {row} of csv not three columns, fix or delete {self.db_path}"
                logger.critical(err)
                raise ValueError(err)
        logger.info("Database checks passed")
