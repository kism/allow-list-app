"""AllowList singleton instance."""

import logging
from pathlib import Path

from allowlistapp.instances.config import get_ala_config
from allowlistapp.services.allowlist import AllowList
from allowlistapp.services.nginx import NGINXAllowlist

logger = logging.getLogger(__name__)

_allowlist: AllowList | None = None
_allowlist_db_path: Path | None = None


def get_allowlist() -> AllowList:
    """Get the AllowList singleton instance."""
    global _allowlist  # noqa: PLW0603
    global _allowlist_db_path  # noqa: PLW0603

    db_path = get_ala_config().app.db_path
    if db_path is None:
        msg = "db_path not configured"
        raise ValueError(msg)

    if _allowlist is None or _allowlist_db_path != db_path:
        nginx_instance = None
        if get_ala_config().services.nginx.enabled:
            nginx_instance = NGINXAllowlist()

        _allowlist = AllowList(nginx_allowlist=nginx_instance)
        _allowlist_db_path = db_path
    return _allowlist


logger.debug("Loaded module: %s", __name__)
