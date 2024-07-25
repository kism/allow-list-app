"""Allowlist object and its friends."""

import datetime
import ipaddress
import logging
import threading
import time

from flask import current_app

from . import database

logger = logging.getLogger(__name__)

nginx_allowlist = None


class AllowList:
    """This is the allowlist object, init from database, query from memory, write to database."""

    def __init__(self, ala_conf: dict) -> None:
        """Initialise the AllowList."""
        self.ala_conf = ala_conf
        self.allowlist = database.db_get_allowlist()

        # See if we need to revert the allowlist daily
        if self.ala_conf["app"]["revert_daily"]:
            thread = threading.Thread(target=self._revert_list_daily, args=(), daemon=True)
            thread.start()

        logger.info("Initialising the database...")
        for subnet in self.ala_conf["app"]["allowed_subnets"]:
            self.add_to_allowlist("default", subnet)
        logger.info("Done initialising the database")

        # For safety since in theory the file can be written to outside of this program
        self._write_app_allowlist_files()

    def is_in_allowlist(self, ip: str) -> bool:
        """Check if ip address is in the allowlist."""
        logger.debug("Checking if IP already in allowlist...")
        auth_in_list = False

        for item in self.allowlist:
            try:
                # Check if the IP matches directly or is within the network
                if ip == item["ip"] or ipaddress.ip_address(ip) in ipaddress.ip_network(item["ip"]):
                    auth_in_list = True
                    break
            except ValueError:
                continue

        return auth_in_list

    def add_to_allowlist(self, username: str, ip: str) -> bool:
        """Insert an IP into the allowlist, returns if an IP has been inserted."""
        logger.debug("Trying to insert ip: %s for user: %s", ip, username)

        added = False
        self._check_ip(ip)

        if self.is_in_allowlist(ip):
            logger.info("Duplicate ip/network, not adding.")
        else:
            new_item = {"username": username, "ip": ip, "date": str(datetime.datetime.now())}
            self.allowlist.append(new_item)
            added = True
            logger.info("Added ip: %s to allowlist", ip)

            database.db_write_allowlist(self.allowlist)
            self._write_app_allowlist_files()

        return added

    def _revert_list_daily(self) -> None:
        """Reset list at 4am."""
        while True:
            logger.info("Adding subnets/ips from config file")

            database.db_reset()

            # Get the current time
            current_time = datetime.datetime.now().time()

            # Set the target time (4 AM)
            target_time = datetime.time(4, 0)

            # Calculate the time difference
            time_difference = datetime.datetime.combine(datetime.date.today(), target_time) - datetime.datetime.combine(
                datetime.date.today(),
                current_time,
            )

            # If the target time is already passed for today, add 1 day
            if time_difference.total_seconds() < 0:
                time_difference += datetime.timedelta(
                    days=1
                )  # pragma: no cover, not going to mock time just for one line of coverage

            seconds_until_next_run = time_difference.total_seconds()

            logger.info(
                "🛌 Reverting allowlist in ~%s minutes",
                str(int(seconds_until_next_run / 60)),
            )

            # Sleep until the target time
            time.sleep(seconds_until_next_run)

            logger.info("It's 4am, reverting IP list to default")

    def _write_app_allowlist_files(self) -> None:
        """Write to the nginx allowlist conf file."""
        if nginx_allowlist:
            nginx_allowlist.write(self.ala_conf, self.allowlist)

    def _check_ip(self, in_ip_or_network: str) -> bool:
        """Check if string is valid IP or Network."""
        valid_ip = False
        for ip_cls in [ipaddress.IPv4Address, ipaddress.IPv4Network, ipaddress.IPv6Address, ipaddress.IPv6Network]:
            try:
                ip_cls(in_ip_or_network)
                valid_ip = True
            except (ipaddress.NetmaskValueError, ipaddress.AddressValueError):
                continue

        if not valid_ip:
            err = f"Invalid IP/network address: {in_ip_or_network}"
            logger.error(err)

        return valid_ip


def start_allowlist_handler() -> None:
    """Start the allowlist handler to handle the allowlists."""
    global nginx_allowlist  # noqa: PLW0603 Needed for how flask loads modules.

    database.start_database()

    if current_app.config["services"]["nginx"]["enabled"]:
        from allowlistapp.al_handler_nginx import NGINXAllowlist

        nginx_allowlist = NGINXAllowlist()


logger.debug("Loaded module: %s", __name__)
