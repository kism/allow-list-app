"""Allowlist object and its friends."""

import datetime
import ipaddress
import threading
import time
from typing import TYPE_CHECKING, Any

from allowlistapp.services.database import Database
from allowlistapp.utils.logger import get_logger

if TYPE_CHECKING:
    from pathlib import Path

    from allowlistapp.services.nginx import NGINXAllowlist

logger = get_logger(__name__)


def normalise_ip(value: str) -> str:
    """Canonical form of an IP or network, host bits are dropped. Raises ValueError if it's neither."""
    value = value.strip()
    if "/" in value:
        return str(ipaddress.ip_network(value, strict=False))

    ip = ipaddress.ip_address(value)
    if isinstance(ip, ipaddress.IPv6Address) and ip.scope_id:
        msg = f"IPv6 scope ids aren't valid in nginx: {value}"
        raise ValueError(msg)
    return str(ip)


def clean_username(username: str) -> str:
    """Drop anything that could end the nginx comment or a log line."""
    return "".join(c for c in username if c.isprintable())


def _contains(outer: str, inner: ipaddress.IPv4Network | ipaddress.IPv6Network) -> bool:
    outer_network = ipaddress.ip_network(outer)
    return outer_network.version == inner.version and inner.subnet_of(outer_network)  # ty: ignore[invalid-argument-type] # Versions checked first


class AllowList:
    """This is the allowlist object, init from database, query from memory, write to database."""

    def __init__(
        self,
        db_path: Path,
        allowed_subnets: list[str],
        *,
        revert_daily: bool,
        nginx_allowlist: NGINXAllowlist | None = None,
    ) -> None:
        """Initialise the AllowList."""
        self._nginx_allowlist = nginx_allowlist
        self._allowed_subnets = allowed_subnets
        # ponytail: one lock around every read, write and nginx reload, plenty at login rates
        self._lock = threading.Lock()

        self._database = Database(db_path)
        self.allowlist: list[dict[str, Any]] = []

        with self._lock:
            # The csv can be edited outside of this program, only keep rows that are safe to write to nginx
            for row in self._database.get_allowlist():
                try:
                    row["ip"] = normalise_ip(row["ip"])
                except ValueError:
                    logger.error("Dropping invalid row from the database: %r", row)  # ruff: ignore[error-instead-of-exception] # Not worth a traceback
                    continue
                row["username"] = clean_username(row["username"])
                self.allowlist.append(row)

            for subnet in allowed_subnets:
                self._add("default", subnet)

            self._write()

        if revert_daily:
            threading.Thread(target=self._revert_list_daily, daemon=True).start()

    def is_in_allowlist(self, ip: str) -> bool:
        """Check if ip address is in the allowlist."""
        try:
            network = ipaddress.ip_network(normalise_ip(ip))
        except ValueError:
            return False

        with self._lock:
            return any(_contains(item["ip"], network) for item in self.allowlist)

    def add_to_allowlist(self, username: str, ip: str) -> bool:
        """Insert an IP into the allowlist, returns if it was inserted. Raises ValueError for an invalid IP."""
        with self._lock:
            added = self._add(username, ip)
            if added:
                self._write()
            return added

    def revert(self) -> None:
        """Reset the allowlist to the default subnets."""
        logger.info("Reverting IP list to default")
        with self._lock:
            self.allowlist = []
            for subnet in self._allowed_subnets:
                self._add("default", subnet)
            self._write()

    def _add(self, username: str, ip: str) -> bool:
        """Add without locking or writing, the caller holds the lock."""
        ip = normalise_ip(ip)
        network = ipaddress.ip_network(ip)

        if any(_contains(item["ip"], network) for item in self.allowlist):
            logger.info("Duplicate ip/network, not adding: %s", ip)
            return False

        self.allowlist.append({"username": clean_username(username), "ip": ip, "date": str(datetime.datetime.now())})
        logger.info("Added ip: %s to allowlist", ip)
        return True

    def _write(self) -> None:
        """Write the database and the nginx allowlist, the caller holds the lock."""
        self._database.write_allowlist(self.allowlist)
        if self._nginx_allowlist:
            self._nginx_allowlist.write(self.allowlist)

    @staticmethod
    def _seconds_until_4am() -> float:
        now = datetime.datetime.now()
        target = datetime.datetime.combine(now.date(), datetime.time(4, 0))
        if target <= now:
            target += datetime.timedelta(days=1)
        return (target - now).total_seconds()

    def _revert_list_daily(self) -> None:
        """Revert the list at 4am, every day."""
        while True:
            seconds = self._seconds_until_4am()
            logger.info("🛌 Reverting allowlist in ~%s minutes", int(seconds / 60))
            time.sleep(seconds)
            self.revert()
