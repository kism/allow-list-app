"""Tests scripts/migrate_config.py, the v0.2 toml to v0.3 json config migration."""

import json
import subprocess  # ruff: ignore[suspicious-subprocess-import] # Runs our own script
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "scripts" / "migrate_config.py"

# The shape of a v0.2 config.toml, as the Flask app wrote it
OLD_TOML = """
[app]
allowed_subnets = ["192.168.1.5/24"]
auth_type = "static"
revert_daily = true
redirect_url = "https://example.com"
db_path = ""

[services.nginx]
enabled = true
allowlist_path = "/etc/nginx/allowlist.conf"

[auth.remote]
url = ""

[auth.static]
password_cleartext = ""
password_hashed = "$argon2id$v=19$m=65536,t=3,p=4$c29tZXNhbHQ$RdescudvJCsgt3ub+b+dWRWJTmaaJObG"

[logging]
level = "INFO"
path = ""

[flask]
DEBUG = false
TESTING = false
"""


def run(*args: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] # Our own script
        [sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True, check=False
    )


def test_migrate(tmp_path: Path) -> None:
    """TEST: Values carry over, empty strings become defaults, flask is dropped, the file is private."""
    toml_path = tmp_path / "config.toml"
    toml_path.write_text(OLD_TOML)

    result = run(toml_path)
    assert result.returncode == 0, result.stderr

    json_path = tmp_path / "config.json"
    config = json.loads(json_path.read_text())
    assert "flask" not in config
    assert config["app"]["allowed_subnets"] == ["192.168.1.0/24"]
    assert config["app"]["redirect_url"] == "https://example.com"
    assert config["app"]["db_path"] is None
    assert config["services"]["nginx"]["allowlist_path"] == "/etc/nginx/allowlist.conf"
    assert config["auth"]["remote"]["url"] is None
    assert config["auth"]["static"]["password_hashed"].startswith("$argon2id$")
    assert config["logging"]["path"] is None
    assert json_path.stat().st_mode & 0o777 == 0o600  # ruff: ignore[magic-value-comparison] # Owner read/write


def test_migrate_no_overwrite(tmp_path: Path) -> None:
    """TEST: An existing config.json is left alone."""
    (tmp_path / "config.toml").write_text(OLD_TOML)
    (tmp_path / "config.json").write_text("{}")

    result = run(tmp_path / "config.toml")
    assert result.returncode != 0
    assert "already exists" in result.stderr
    assert (tmp_path / "config.json").read_text() == "{}"


def test_migrate_invalid(tmp_path: Path) -> None:
    """TEST: A config that won't validate (no password) leaves nothing behind, into a separate instance dir."""
    (tmp_path / "config.toml").write_text('[app]\nauth_type = "static"\n')

    result = run(tmp_path / "config.toml", tmp_path / "instance")
    assert result.returncode != 0
    assert "doesn't validate" in result.stderr
    assert not (tmp_path / "instance" / "config.json").exists()
