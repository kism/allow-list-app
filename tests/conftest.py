"""The conftest.py file serves as a means of providing fixtures for an entire directory.

Fixtures defined in a conftest.py can be used by any test in that package without needing to import them.
"""

import os

import flask
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

    import os

    assert not os.path.exists(os.path.join(os.getcwd(), "test.csv")), "HERHEHRHEHRE"

    yield create_app(get_test_config("testing_true_valid"), instance_path=tmp_path)

    assert not os.path.exists(os.path.join(os.getcwd(), "test.csv")), "HERHEHRHEHRE____AFTER"


@pytest.fixture()
def client(tmp_path, get_test_config) -> any:
    """This returns a test client for the default app()."""
    app = create_app(get_test_config("testing_true_valid"), instance_path=tmp_path)

    assert not os.path.exists(os.path.join(os.getcwd(), "test.csv")), "HERHEHRHEHRE"

    yield app.test_client()

    assert not os.path.exists(os.path.join(os.getcwd(), "test.csv")), "HERHEHRHEHRE____AFTER"


@pytest.fixture()
def runner() -> any:
    """TODO?????"""
    return app.test_cli_runner()


@pytest.fixture()
def get_test_config() -> dict:
    """Function returns a function, which is how it needs to be."""

    def _get_test_config(config_name: str) -> dict:
        """Load all the .toml configs into a single dict."""
        out_config = None

        filename = f"{config_name}.toml"

        filepath = os.path.join(TEST_CONFIGS_LOCATION, filename)

        if os.path.isfile(filepath):
            with open(filepath) as file:
                out_config = tomlkit.load(file)

        return out_config

    return _get_test_config
