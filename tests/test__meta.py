"""Test versioning and file generation."""

import tomllib
from pathlib import Path

from allowlistapp.version import __version__


def test_version_pyproject() -> None:
    """Verify version in pyproject.toml matches package version."""
    pyproject_path = Path("pyproject.toml")
    with pyproject_path.open("rb") as f:
        pyproject_toml = tomllib.load(f)
    assert pyproject_toml.get("project", {}).get("version") == __version__, (
        "Version in pyproject.toml does not match package version."
    )


def test_version_lock() -> None:
    """Verify version in uv.lock matches package version."""
    lock_path = Path("uv.lock")
    with lock_path.open("rb") as f:
        uv_lock = tomllib.load(f)

    package = next((pkg for pkg in uv_lock.get("package", []) if pkg["name"] == "allowlistapp"), None)
    assert package is not None, "allowlistapp not found in uv.lock"
    assert package["version"] == __version__
