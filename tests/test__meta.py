"""Test versioning."""

import tomllib
from pathlib import Path

from allowlistapp import PROGRAM_NAME, PROGRAM_REPO_URL, PROGRAM_VERSION, constants


def test_version_pyproject() -> None:
    """Verify version in pyproject.toml matches package version."""
    with Path("pyproject.toml").open("rb") as f:
        pyproject_toml = tomllib.load(f)
    assert pyproject_toml.get("project", {}).get("version", None) == PROGRAM_VERSION


def test_version_lock() -> None:
    """Verify version in uv.lock matches package version."""
    with Path("uv.lock").open("rb") as f:
        uv_lock = tomllib.load(f)

    found_version = False
    for package in uv_lock.get("package", []):
        if package.get("name") == PROGRAM_NAME:
            assert package.get("version") == PROGRAM_VERSION
            found_version = True
            break

    assert found_version, f"{PROGRAM_NAME} not found in uv.lock"


def test_repo_url() -> None:
    """Verify repo URL is correct."""
    with Path("pyproject.toml").open("rb") as f:
        pyproject_toml = tomllib.load(f)
    assert pyproject_toml.get("project", {}).get("urls", {}).get("Repository", None) == PROGRAM_REPO_URL


def test_get_version_str_with_git(tmp_path, monkeypatch) -> None:
    """Verify branch and commit are read from a git dir next to the package."""
    git_dir = tmp_path / ".git"
    (git_dir / "logs").mkdir(parents=True)
    (git_dir / "logs" / "HEAD").write_text("0000000 abcdef1234567 Someone <a@b.c> 0 +0000\tcommit: hello\n")
    (git_dir / "HEAD").write_text("ref: refs/heads/my-branch\n")
    monkeypatch.setattr(constants, "__file__", str(tmp_path / "pkg" / "constants.py"))

    assert constants._get_version_str() == f"{PROGRAM_NAME} v{PROGRAM_VERSION}-my-branch/abcdef1"


def test_get_version_str_no_git(tmp_path, monkeypatch) -> None:
    """Verify version string without a git dir."""
    monkeypatch.setattr(constants, "__file__", str(tmp_path / "pkg" / "constants.py"))

    assert constants._get_version_str() == f"{PROGRAM_NAME} v{PROGRAM_VERSION}"
