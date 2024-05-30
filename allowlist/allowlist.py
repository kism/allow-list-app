#!/usr/bin/env python3
"""Flask webapp to control a nginx allowlist."""

import datetime
import ipaddress
import logging
import os
import pwd
import subprocess
import time

logger = logging.getLogger("allowlist")


class NGINXAllowlistWriter:
    """Object to handle writing NGINX allowlist."""

    def __init__(self) -> True:
        """Init settings for the NGINX Allowlist Writer."""
        self.writing = False

    def __check_allowlist(self, in_conf: str) -> str:
        """Validate the list."""
        errors_occurred = False
        words_per_line = 2
        out_conf = "deny all;"

        lines = in_conf.splitlines()
        lines.append("deny all;")
        lines = list(set(lines))
        lines.sort()

        for line in lines:
            words = line.split(" ")
            if words[0] not in ["allow", "deny"]:
                logger.error("❌ First word in line isn't allow or deny: %s", line)
                errors_occurred = True

            if words[0] == "allow":
                ip_to_check = words[1].replace(";", "")
                if not self.__check_ip(ip_to_check):
                    logger.error("❌ Invalid IP address/network: %s", line)
                    errors_occurred = True

            if line[-1] != ";":
                logger.error("❌ No ';' at end of line: %s", line)
                errors_occurred = True

            if len(words) != words_per_line:
                logger.error("❌ Word count validation failed for line: %s", line)
                errors_occurred = True

        if not errors_occurred:
            out_conf = "\n".join(lines)
        else:
            logger.error('❌ Line validation failed, reverting to "deny all;" ')

        return out_conf

    def __check_ip(self, in_ip_or_network: str) -> bool:
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

        return one_success

    def write(self, ala_settings: dict, ip: str) -> None:
        """Write NGINX allowlist."""
        logger.debug("Writing allowlist: %s", ala_settings.allowlist_path)
        while self.writing:
            time.sleep(1)

        self.writing = True
        with open(ala_settings.allowlist_path, encoding="utf8") as conf_file:
            content = conf_file.read()

        with open(ala_settings.allowlist_path, "w", encoding="utf8") as conf_file:
            content = "allow " + ip + ";\n" + content
            content = self.__check_allowlist(content)
            logger.debug("Content to write: \n %s", content)
            conf_file.write(content)
            logger.info("Wrote config, allowing: %s", ip)
        self.writing = False
        logger.debug("Finished writing allowlist")
        nginx_reloader.reload()

    def revert(self, ala_settings: dict) -> None:
        """Write NGINX allowlist."""
        # Revert list
        while self.writing:
            time.sleep(1)
        self.writing = True
        with open(ala_settings.allowlist_path, "w", encoding="utf8") as conf_file:
            conf_file.write("deny all;")
        self.writing = False

        for subnet in ala_settings.allowed_subnets:
            write_allowlist_file(ala_settings, subnet)


class NGINXReloader:
    """Object to handle reloading NGINX."""

    def __init__(self) -> True:
        """Init settings for the NGINX Reloader."""
        self.nginx_reloading = False
        self.user_account = pwd.getpwuid(os.getuid())[0]

        self.reload_nginx_command = ["systemctl", "reload", "nginx"]
        if self.user_account != "root":
            self.reload_nginx_command = ["sudo", "systemctl", "reload", "nginx"]

    def reload(self) -> None:
        """Reload NGINX."""
        while self.nginx_reloading:
            time.sleep(1)

        self.nginx_reloading = True
        logger.info("Reloading nginx")
        result = None
        try:
            result = subprocess.run(self.reload_nginx_command, check=True, capture_output=True, text=True)  # noqa: S603 Input has been validated
        except subprocess.CalledProcessError:
            err = (
                "❌ Couldnt restart nginx, either: \n"
                "Nginx isnt installed\n"
                "or\n"
                f"Sudoers rule not created for this user ({self.user_account})\n"
                "Create and edit a sudoers file\n"
                f" visudo /etc/sudoers.d/{self.user_account}\n"
                f"And insert the text: {self.user_account} ALL=(root) NOPASSWD: /usr/sbin/systemctl reload nginx...\n\n"
            )
            if result:
                err += f"stderr: \n{result.stderr}"
            logger.exception(err)

        finally:
            self.nginx_reloading = False


def write_allowlist_file(ala_settings: dict, ip: str) -> None:
    """Write to the nginx allowlist conf file."""
    nginx_allowlist_writer.write(ala_settings, ip)


def revert_list_daily(ala_settings: dict) -> None:
    """Reset list at 4am."""
    while True:
        logger.info("Adding subnets/ips from config file")

        nginx_allowlist_writer.revert(ala_settings)

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


nginx_reloader = NGINXReloader()
nginx_allowlist_writer = NGINXAllowlistWriter()
