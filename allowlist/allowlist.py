#!/usr/bin/env python3
"""Flask webapp to control a nginx allowlist."""

import datetime
import logging
import os
import pwd
import subprocess
import time

from jinja2 import Environment, FileSystemLoader

from . import database, get_ala_settings

ala_settings = get_ala_settings()
logger = logging.getLogger("allowlist")


class NGINXAllowlistWriter:
    """Object to handle writing NGINX allowlist."""

    def __init__(self) -> True:
        """Init settings for the NGINX Allowlist Writer."""
        self.writing = False

    def write(self, ala_settings: dict, allowlist: list) -> None:
        """Write NGINX allowlist."""
        logger.debug("Writing nginx allowlist: %s", ala_settings.allowlist_path)
        while self.writing:
            time.sleep(1)

        env = Environment(loader=FileSystemLoader(f"allowlist{os.sep}templates"), autoescape=True)
        template = env.get_template("nginx.conf.j2")
        rendered_template = template.render(allowlist=allowlist)

        with open(ala_settings.allowlist_path, "w", encoding="utf8") as conf_file:
            conf_file.write(rendered_template)

        self.writing = False
        logger.debug("Finished writing nginx allowlist")
        nginx_reloader.reload()


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


def add_to_allowlist(ala_settings: dict, username: str, ip: str) -> True:
    """Write to the nginx allowlist conf file."""
    change = database.insert_ip(username, ip)
    if change:
        write_allowlist_files(ala_settings)


def write_allowlist_files(ala_settings: dict) -> None:
    """Write to the nginx allowlist conf file."""
    allowlist = database.get_allowlist()

    if nginx_allowlist_writer:
        nginx_allowlist_writer.write(ala_settings, allowlist)


def revert_list_daily(ala_settings: dict) -> None:
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


nginx_reloader = None
nginx_allowlist_writer = None
if "nginx" in ala_settings.services:
    nginx_reloader = NGINXReloader()
    nginx_allowlist_writer = NGINXAllowlistWriter()
