"""Module to handle writing the nginx allowlist and reloading nginx."""

import getpass
import subprocess  # ruff: ignore[suspicious-subprocess-import] # Fixed command, no user input
from typing import TYPE_CHECKING, Any

from jinja2 import Environment, FileSystemLoader

from allowlistapp.constants import TEMPLATES_DIR
from allowlistapp.utils.logger import get_logger

if TYPE_CHECKING:
    from pathlib import Path

logger = get_logger(__name__)


class NGINXAllowlist:
    """Writes the NGINX allowlist, the AllowList's lock keeps writes and reloads one at a time."""

    def __init__(self, allowlist_path: Path) -> None:
        """Init config for the NGINX Allowlist Writer."""
        self.allowlist_path = allowlist_path
        self.user_account = getpass.getuser()

        self.reload_nginx_command = ["systemctl", "reload", "nginx"]
        if self.user_account != "root":
            self.reload_nginx_command = ["sudo", "systemctl", "reload", "nginx"]

        # Not HTML, so no HTML escaping. The AllowList only hands over normalised IPs and printable usernames.
        env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=False)  # ruff: ignore[jinja2-autoescape-false] # Not HTML
        self._template = env.get_template("nginx.conf.j2")

    def write(self, allowlist: list[dict[str, Any]]) -> None:
        """Write NGINX allowlist, then reload nginx."""
        logger.debug("Writing nginx allowlist: %s", self.allowlist_path)

        try:
            self.allowlist_path.write_text(self._template.render(allowlist=allowlist), encoding="utf8")
        except FileNotFoundError as exc:
            msg = f"Could not write NGINX allowlist file to path: {self.allowlist_path}"
            logger.exception(msg)
            raise FileNotFoundError(msg) from exc

        logger.debug("Finished writing nginx allowlist")
        self._reload()

    def _reload(self) -> None:
        """Reload NGINX."""
        logger.info("Reloading nginx")
        try:
            subprocess.run(self.reload_nginx_command, check=True, capture_output=True, text=True)  # ruff: ignore[subprocess-without-shell-equals-true] Fixed command
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
