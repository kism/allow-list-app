"""Module to handle writing the nginx allowlist and reloading nginx."""

import logging
import os
import pwd
import subprocess
import time

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)


class NGINXAllowlist:
    """Object to handle writing NGINX allowlist."""

    def __init__(self) -> True:
        """Init config for the NGINX Allowlist Writer."""
        # Monitor Writing
        self._writing = False

        # Monitor Reloading
        self._nginx_reloading = False
        self.user_account = pwd.getpwuid(os.getuid())[0]

        self.reload_nginx_command = ["systemctl", "reload", "nginx"]
        if self.user_account != "root":
            self.reload_nginx_command = ["sudo", "systemctl", "reload", "nginx"]

    def write(self, ala_conf: dict, allowlist: list) -> None:
        """Write NGINX allowlist."""
        logger.debug("Writing nginx allowlist: %s", ala_conf["app"]["allowlist_path"])
        while self._writing:
            time.sleep(1)

        env = Environment(
            loader=FileSystemLoader(os.path.join(os.getcwd(), "allowlistapp", "templates")), autoescape=True
        )
        template = env.get_template("nginx.conf.j2")
        rendered_template = template.render(allowlist=allowlist)

        with open(ala_conf["app"]["allowlist_path"], "w", encoding="utf8") as conf_file:
            conf_file.write(rendered_template)

        self._writing = False
        logger.debug("Finished writing nginx allowlist")
        self._reload()

    def _reload(self) -> None:
        """Reload NGINX."""
        while self._nginx_reloading:
            time.sleep(1)

        self._nginx_reloading = True
        logger.info("Reloading nginx")
        try:
            subprocess.run(self.reload_nginx_command, check=True, capture_output=True, text=True)  # noqa: S603 Input has been validated
            logger.info("Nginx reloaded")
        except subprocess.CalledProcessError:
            err = (
                "❌ Couldn't restart nginx, either: \n"
                "Nginx isn't installed\n"
                "or\n"
                f"Sudoers rule not created for this user ({self.user_account})\n"
                "Create and edit a sudoers file\n"
                f" visudo /etc/sudoers.d/{self.user_account}\n"
                f"And insert the text: {self.user_account} ALL=(root) NOPASSWD: /usr/sbin/systemctl reload nginx...\n\n"
            )
            logger.exception(err)

        finally:
            self._nginx_reloading = False


logger.debug("Loaded module: %s", __name__)
