"""Test ngnix reloading."""

import logging

import pytest


def test_nginx_reload(allowlistapp: any, get_test_config: dict, caplog: pytest.LogCaptureFixture):
    """Unit test _warn_unexpected_keys."""
    caplog.set_level(logging.ERROR)

    allowlistapp.create_app(get_test_config("nginx_valid"), instance_path=pytest.TEST_INSTANCE_PATH)

    assert "Couldn't restart nginx" in caplog.text
