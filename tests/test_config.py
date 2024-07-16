"""Test launching the app and config."""

import contextlib
import logging
import os
import shutil

import pytest

from allowlistapp import create_app


def test_config_valid(get_test_config: dict):
    """Test passing config to app."""
    # TEST: Assert that the config dictionary can set config attributes successfully.
    assert not create_app(
        get_test_config("testing_false_valid")
    ).testing, "Flask testing config item not being set correctly."
    assert create_app(
        get_test_config("testing_true_valid")
    ).testing, "Flask testing config item not being set correctly."


def test_config_invalid(get_test_config: dict):
    """Test that program exits when given invalid config."""
    # TEST: Assert that the program exists when provided an invalid config dictionary.
    with pytest.raises(SystemExit) as exc_info:
        create_app(get_test_config("invalid"))

    assert isinstance(exc_info.type, type(SystemExit)), "App did not exit on config validation failure."
    assert exc_info.value.code == 1, "App did not have correct exit code for config validation failure."


def test_config_file_creation(get_test_config: dict, caplog: pytest.LogCaptureFixture):
    """Tests relating to config file."""
    # TEST: that file is created when no config is provided.
    caplog.set_level(logging.WARNING)
    create_app(test_config=None, instance_path=pytest.TEST_INSTANCE_PATH)
    assert "No configuration file found, creating at default location:" in caplog.text
    caplog.clear()

    # TEST: that file is not created when config is provided.
    caplog.set_level(logging.WARNING)
    create_app(test_config=get_test_config("testing_true_valid"), instance_path=pytest.TEST_INSTANCE_PATH)
    assert "No configuration file found, creating at default location:" not in caplog.text


def test_config_file_loading(caplog: pytest.LogCaptureFixture):
    """Tests relating to config file."""
    shutil.copy(os.path.join(pytest.TEST_CONFIGS_LOCATION, "testing_true_valid.toml"), pytest.TEST_CONFIG_FILE_PATH)

    # TEST: that file is created when no config is provided.
    caplog.set_level(logging.INFO)
    create_app(test_config=None, instance_path=pytest.TEST_INSTANCE_PATH)
    assert "Using this path as it's the first one that was found" in caplog.text
    caplog.clear()

    # Remove any created config/logs
    with contextlib.suppress(FileNotFoundError):
        os.unlink(pytest.TEST_CONFIG_FILE_PATH)
