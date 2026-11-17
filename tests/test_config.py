"""Tests config loading and writing."""

import json
from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from allowlistapp.config import CONFIG_FILE_NAME, Config

if TYPE_CHECKING:
    from pathlib import Path


def test_load_missing_config(tmp_path: Path) -> None:
    """TEST: A missing config file gets written out with defaults, then fails as there is no password."""
    with pytest.raises(ValidationError, match=r"set auth\.static\.password_cleartext"):
        Config.load(tmp_path)

    config = json.loads((tmp_path / CONFIG_FILE_NAME).read_text())
    assert config["app"]["auth_type"] == "static"
    assert not config["auth"]["static"]["password_cleartext"]


def test_password_hashed_and_written_back(tmp_path: Path) -> None:
    """TEST: A cleartext password is hashed, and only the hash is written back."""
    config_path = tmp_path / CONFIG_FILE_NAME
    config_path.write_text('{"auth": {"static": {"password_cleartext": "hunter2"}}}')

    config = Config.load(tmp_path)
    assert not config.auth.static.password_cleartext
    assert config.auth.static.password_hashed.startswith("$argon2")

    written = json.loads(config_path.read_text())
    assert "hunter2" not in config_path.read_text()
    assert written["auth"]["static"]["password_hashed"] == config.auth.static.password_hashed

    # Loading again keeps the hash
    assert Config.load(tmp_path).auth.static.password_hashed == config.auth.static.password_hashed


@pytest.mark.parametrize(
    ("config_json", "error"),
    [
        ('{"app": {"auth_type": "jellyfin"}}', "set auth.remote.url"),
        ('{"app": {"auth_type": "nope"}}', "auth_type"),
        ('{"app": {"auth_type": "jellyfin"}, "auth": {"remote": {"url": "jf.example.com"}}}', "url"),
        ('{"auth": {"static": {"password_hashed": "hunter2"}}}', "isn't an argon2 hash"),
        ('{"app": {"allowed_subnets": ["nope"]}, "auth": {"static": {"password_cleartext": "x"}}}', "allowed_subnets"),
        (
            '{"auth": {"static": {"password_cleartext": "x"}}, "services": {"nginx": {"enabled": true}}}',
            "allowlist_path must be set",
        ),
    ],
)
def test_invalid_config(tmp_path: Path, config_json: str, error: str) -> None:
    """TEST: Invalid configs fail validation."""
    (tmp_path / CONFIG_FILE_NAME).write_text(config_json)

    with pytest.raises(ValidationError, match=error):
        Config.load(tmp_path)


def test_config_file_private(tmp_path: Path) -> None:
    """TEST: The config file holds the password hash, so only the owner can read it, even if it existed already."""
    config_path = tmp_path / CONFIG_FILE_NAME
    config_path.write_text('{"auth": {"static": {"password_cleartext": "hunter2"}}}')
    config_path.chmod(0o644)

    Config.load(tmp_path)
    assert config_path.stat().st_mode & 0o777 == 0o600  # ruff: ignore[magic-value-comparison] # Owner read/write


def test_allowed_subnets_normalised(tmp_path: Path) -> None:
    """TEST: Subnets with host bits load, instead of crashing startup."""
    (tmp_path / CONFIG_FILE_NAME).write_text(
        '{"app": {"allowed_subnets": ["192.168.1.5/24"]}, "auth": {"static": {"password_cleartext": "x"}}}'
    )
    assert Config.load(tmp_path).app.allowed_subnets == ["192.168.1.0/24"]
