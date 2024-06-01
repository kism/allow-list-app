"""Allowlist object and its friends."""

import ipaddress
import logging
import threading
import time
from datetime import datetime

from . import database, get_ala_settings

ala_settings = get_ala_settings()
logger = logging.getLogger("allowlist")


nginx_allowlist = None
if "nginx" in ala_settings.services:
    from allowlist.allowlist_app_nginx import NGINXAllowlist

    nginx_allowlist = NGINXAllowlist()


class AllowList:
    """This is the allowlist object, init from database, query from memory, write to database."""

    def __init__(self, ala_settings: dict) -> None:
        """Initialise the AllowList."""
        database.db_check()
        self.ala_settings = ala_settings
        self.allowlist = database.db_get_allowlist()

        # See if we need to revert the allowlist daily
        if self.ala_settings.revert_daily:
            thread = threading.Thread(target=self.__revert_list_daily, args=(), daemon=True)
            thread.start()

        logging.info("Initialising the database...")
        for subnet in self.ala_settings.allowed_subnets:
            self.add_to_allowlist("default", subnet)
        logging.info("Done initialising the database")

    def is_in_allowlist(self, ip: str) -> bool:
        """Check if ip addres is in the allowlist."""
        logger.debug("Checking if IP allready in allowlist...")
        auth_in_list = False
        for item in self.allowlist:
            if item["ip"] == ip:
                auth_in_list = True
                break

        return auth_in_list

    def add_to_allowlist(self, username: str, ip: str) -> bool:
        """Insert an IP into the allowlist, returns if an IP has been inserted."""
        logger.debug("Trying to insert ip: %s for user: %s", ip, username)

        added = False
        self.__check_ip(ip)

        if self.is_in_allowlist(ip):
            logger.info("Duplicate auth! Not adding.")
        else:
            new_item = {"username": username, "ip": ip, "date": str(datetime.now())}
            self.allowlist.append(new_item)
            added = True
            logger.info("Added ip: %s to allowlist", ip)

        database.db_write_allowlist(self.allowlist)
        self.__write_allowlist_files()

        return added

    def __revert_list_daily(self) -> None:
        """Reset list at 4am."""
        while True:
            logger.info("Adding subnets/ips from config file")

            database.reset_database()
            database.init_database(ala_settings)

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
                time_difference += datetime.timedelta(days=1)

            seconds_until_next_run = time_difference.total_seconds()

            logger.info(
                "🛌 Reverting allowlist in ~%s minutes",
                str(int(seconds_until_next_run / 60)),
            )

            # Sleep until the target time
            time.sleep(seconds_until_next_run)

            logger.info("It's 4am, reverting IP list to default")

    def __write_allowlist_files(self) -> None:
        """Write to the nginx allowlist conf file."""
        if nginx_allowlist:
            nginx_allowlist.write(self.ala_settings, self.allowlist)

    def __check_ip(self, in_ip_or_network: str) -> True:
        """Check if string is valid IP or Network."""
        one_success = False
        try:
            ipaddress.IPv4Address(in_ip_or_network)
            one_success = True
        except ipaddress.NetmaskValueError:
            pass
        except ipaddress.AddressValueError:
            pass

        try:
            ipaddress.IPv4Network(in_ip_or_network)
            one_success = True
        except ipaddress.NetmaskValueError:
            pass
        except ipaddress.AddressValueError:
            pass

        try:
            ipaddress.IPv6Address(in_ip_or_network)
            one_success = True
        except ipaddress.AddressValueError:
            pass

        try:
            ipaddress.IPv6Network(in_ip_or_network)
            one_success = True
        except ipaddress.NetmaskValueError:
            pass
        except ipaddress.AddressValueError:
            pass

        if not one_success:
            err = f"Invalid IP/network address: {in_ip_or_network}"
            raise ValueError(err)
