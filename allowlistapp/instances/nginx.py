"""NGINXAllowlist singleton instance."""

import logging

from allowlistapp.services.nginx import NGINXAllowlist

logger = logging.getLogger(__name__)

_nginx_allowlist: NGINXAllowlist | None = None


def get_nginx_allowlist() -> NGINXAllowlist | None:
    """Get the NGINXAllowlist singleton instance."""
    return _nginx_allowlist


def init_nginx() -> None:
    """Initialize the NGINXAllowlist singleton."""
    global _nginx_allowlist  # noqa: PLW0603
    _nginx_allowlist = NGINXAllowlist()


logger.debug("Loaded module: %s", __name__)
