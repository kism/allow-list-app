"""Test ngnix reloading."""

import logging
import time

import pytest

from allowlistapp import create_app


def test_nginx_reload_failure(fp, tmp_path, get_test_config, caplog: pytest.LogCaptureFixture):
    """Test that nginx reload fails, assumes that nginx isn't on the host testing this lol."""
    fp.register(["sudo", "systemctl", "reload", "nginx"], returncode=1)
    create_app(get_test_config("valid_nginx.toml"), tmp_path)
    with caplog.at_level(logging.INFO):
        assert "Reverting allowlist in" in caplog.text
        assert "Couldn't restart nginx" in caplog.text


def test_nginx_reload_success(fp, tmp_path, get_test_config, caplog: pytest.LogCaptureFixture):
    """Test that reload works."""
    fp.register(["sudo", "systemctl", "reload", "nginx"], returncode=0)
    create_app(get_test_config("valid_nginx.toml"), tmp_path)

    with caplog.at_level(logging.INFO):
        assert "Nginx reloaded" in caplog.text


@pytest.fixture()
def sleepless(monkeypatch):
    """Patched function for no sleep."""

    def sleep(seconds) -> None:
        """No sleep."""

    monkeypatch.setattr(time, "sleep", sleep)


def test_nginx_reload_revert_daily(sleepless, fp, tmp_path, get_test_config, caplog: pytest.LogCaptureFixture):
    """Test that reload works."""
    fp.register(["sudo", "systemctl", "reload", "nginx"], returncode=0)
    create_app(get_test_config("valid_nginx.toml"), tmp_path)

    with caplog.at_level(logging.INFO):
        assert "It's 4am, reverting IP list to default" in caplog.text
