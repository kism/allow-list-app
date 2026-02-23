"""NGINXAllowlist singleton instance."""

import logging

from allowlistapp.services.nginx import NGINXAllowlist

logger = logging.getLogger(__name__)

_nginx_allowlist: NGINXAllowlist | None = None


def get_nginx_allowlist() -> NGINXAllowlist | None:
    """Get the NGINXAllowlist singleton instance."""
    global _nginx_allowlist  # noqa: PLW0603

    if _nginx_allowlist is None:
        _nginx_allowlist = NGINXAllowlist()

    return _nginx_allowlist


logger.debug("Loaded module: %s", __name__)
