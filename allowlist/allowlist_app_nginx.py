"""Module to handle writing the nginx allowlist and reloading nginx."""

import logging
import os
import pwd
import subprocess
import time

from jinja2 import Environment, FileSystemLoader

from . import get_ala_settings

ala_sett = get_ala_settings()

logger = logging.getLogger(__name__)


class NGINXAllowlist:
    """Object to handle writing NGINX allowlist."""

    def __init__(self) -> True:
        """Init settings for the NGINX Allowlist Writer."""
        # Monitor Writing
        self.writing = False

        # Monitor Reloading
        self.nginx_reloading = False
        self.user_account = pwd.getpwuid(os.getuid())[0]

        self.reload_nginx_command = ["systemctl", "reload", "nginx"]
        if self.user_account != "root":
            self.reload_nginx_command = ["sudo", "systemctl", "reload", "nginx"]

    def write(self, ala_sett: dict, allowlist: list) -> None:
        """Write NGINX allowlist."""
        logger.debug("Writing nginx allowlist: %s", ala_sett.allowlist_path)
        while self.writing:
            time.sleep(1)

        env = Environment(loader=FileSystemLoader(f"allowlist{os.sep}templates"), autoescape=True)
        template = env.get_template("nginx.conf.j2")
        rendered_template = template.render(allowlist=allowlist)

        with open(ala_sett.allowlist_path, "w", encoding="utf8") as conf_file:
            conf_file.write(rendered_template)

        self.writing = False
        logger.debug("Finished writing nginx allowlist")
        self.__reload()

    def __reload(self) -> None:
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
