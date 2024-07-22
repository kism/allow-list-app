"""The conftest.py file serves as a means of providing fixtures for an entire directory.

Fixtures defined in a conftest.py can be used by any test in that package without needing to import them.
"""

import os

import pytest
import tomlkit

from allowlistapp import create_app

TEST_CONFIGS_LOCATION = os.path.join(os.getcwd(), "tests", "configs")


def pytest_configure():
    """This is a magic function for adding things to pytest?"""
    pytest.TEST_CONFIGS_LOCATION = TEST_CONFIGS_LOCATION


@pytest.fixture()
def app(tmp_path, get_test_config) -> any:
    """This fixture uses the default config within the flask app."""
    return create_app(get_test_config("testing_true_valid.toml"), instance_path=tmp_path)


@pytest.fixture()
def client(app) -> any:
    """This returns a test client for the default app()."""
    return app.test_client()


@pytest.fixture()
def runner() -> any:
    """TODO?????"""
    return app.test_cli_runner()


@pytest.fixture()
def get_test_config() -> dict:
    """Function returns a function, which is how it needs to be."""

    def _get_test_config(config_name: str) -> dict:
        """Load all the .toml configs into a single dict."""
        filepath = os.path.join(TEST_CONFIGS_LOCATION, config_name)

        with open(filepath) as file:
            return tomlkit.load(file)

    return _get_test_config
