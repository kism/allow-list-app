"""The conftest.py file serves as a means of providing fixtures for an entire directory.

Fixtures defined in a conftest.py can be used by any test in that package without needing to import them.
"""

import os
from collections.abc import Callable

import pytest
import tomlkit
from flask import Flask
from flask.testing import FlaskClient, FlaskCliRunner

from allowlistapp import create_app

TEST_CONFIGS_LOCATION = os.path.join(os.getcwd(), "tests", "configs")


@pytest.fixture()
def app(tmp_path, get_test_config) -> Flask:
    """This fixture uses the default config within the flask app."""
    return create_app(get_test_config("valid_testing_true.toml"), instance_path=tmp_path)


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    """This returns a test client for the default app()."""
    return app.test_client()


@pytest.fixture()
def client_url_auth(tmp_path, get_test_config) -> FlaskClient:
    """This fixture uses the default config within the flask app."""
    from allowlistapp import create_app

    app = create_app(get_test_config("valid_url_auth_url.toml"), instance_path=tmp_path)

    return app.test_client()


@pytest.fixture()
def runner(app: Flask) -> FlaskCliRunner:
    """TODO?????"""
    return app.test_cli_runner()


@pytest.fixture()
def get_test_config() -> Callable:
    """Function returns a function, which is how it needs to be."""

    def _get_test_config(config_name: str) -> dict:
        """Load all the .toml configs into a single dict."""
        filepath = os.path.join(TEST_CONFIGS_LOCATION, config_name)

        with open(filepath) as file:
            return tomlkit.load(file)

    return _get_test_config


@pytest.fixture()
def place_test_config(get_test_config) -> Callable:
    """Function returns a function, which is how it needs to be."""

    def _place_test_config(config_name: str, out_path: str) -> None:
        """Place a test config in the tmp_path."""
        filepath = os.path.join(TEST_CONFIGS_LOCATION, config_name)

        with open(filepath) as file:
            config = tomlkit.load(file)

        with open(os.path.join(out_path, "config.toml"), "w") as file:
            tomlkit.dump(config, file)

    return _place_test_config
