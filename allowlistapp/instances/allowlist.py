"""AllowList singleton instance."""

import logging

from allowlistapp.instances import database
from allowlistapp.instances.config import get_ala_config
from allowlistapp.instances.nginx import get_nginx_allowlist, init_nginx
from allowlistapp.services.allowlist import AllowList

logger = logging.getLogger(__name__)

_allowlist: AllowList | None = None


def get_allowlist() -> AllowList:
    """Get the AllowList singleton instance."""
    if _allowlist is None:
        msg = "AllowList not initialized, call init_allowlist() first"
        raise ValueError(msg)
    return _allowlist


def init_allowlist() -> None:
    """Initialize the AllowList singleton."""
    global _allowlist  # noqa: PLW0603
    _allowlist = None

    database.start_database()

    nginx_instance = None
    if get_ala_config().services.nginx.enabled:
        init_nginx()
        nginx_instance = get_nginx_allowlist()

    _allowlist = AllowList(nginx_instance)


logger.debug("Loaded module: %s", __name__)
