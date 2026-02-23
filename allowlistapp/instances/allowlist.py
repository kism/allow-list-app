"""AllowList singleton instance."""

import logging

from allowlistapp.instances.config import get_ala_config
from allowlistapp.instances.nginx import get_nginx_allowlist
from allowlistapp.services.allowlist import AllowList

logger = logging.getLogger(__name__)

_allowlist: AllowList | None = None


def get_allowlist() -> AllowList:
    """Get the AllowList singleton instance."""
    global _allowlist  # noqa: PLW0603

    if _allowlist is None:
        if get_ala_config().services.nginx.enabled:
            nginx_instance = get_nginx_allowlist()

        _allowlist = AllowList(nginx_allowlist=nginx_instance)
    return _allowlist


logger.debug("Loaded module: %s", __name__)
