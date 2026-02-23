"""AllowListAppConfig singleton."""

from pathlib import Path
from typing import Any

from allowlistapp.config import AllowListAppConfig

_ala_conf: AllowListAppConfig | None = None


def get_ala_config(
    instance_path: Path | None = None,
    config_data: dict[str, Any] | None = None,
) -> AllowListAppConfig:
    """Get the global AllowListAppConfig instance.

    If instance_path is provided, always reload (supports testing).
    If not provided, return cached instance.
    """
    global _ala_conf  # noqa: PLW0603
    if _ala_conf is None or instance_path is not None:
        if instance_path is None:
            msg = "instance_path must be provided the first time get_ala_config is called"
            raise ValueError(msg)
        _ala_conf = AllowListAppConfig.load(instance_path=instance_path, config_data=config_data)
    return _ala_conf
