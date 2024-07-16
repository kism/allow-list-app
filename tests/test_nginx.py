"""Test ngnix reloading."""

import logging

import pytest
from flask import Flask


def test_nginx_reload(allowlistapp: any, get_test_config: dict, caplog: pytest.LogCaptureFixture):
    """Unit test _warn_unexpected_keys."""
    with caplog.at_level(logging.INFO):
        app = allowlistapp.create_app(get_test_config("nginx_valid"), instance_path=pytest.TEST_INSTANCE_PATH)

        assert type(app) == Flask

        assert "Couldn't restart nginx" in caplog.text
