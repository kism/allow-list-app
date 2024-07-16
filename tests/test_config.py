"""Test launching the app and config."""

import logging
import os
import shutil

import pytest

from allowlistapp import config, create_app


def test_config_valid(allowlistapp: any, get_test_config: dict):
    """Test passing config to app."""
    # TEST: Assert that the config dictionary can set config attributes successfully.
    assert not allowlistapp.create_app(
        get_test_config("testing_false_valid"), instance_path=pytest.TEST_INSTANCE_PATH
    ).testing, "Flask testing config item not being set correctly."
    assert allowlistapp.create_app(
        get_test_config("testing_true_valid"), instance_path=pytest.TEST_INSTANCE_PATH
    ).testing, "Flask testing config item not being set correctly."


def test_config_invalid(get_test_config: dict):
    """Test that program exits when given invalid config."""
    # TEST: Assert that the program exists when provided an invalid config dictionary.
    with pytest.raises(config.ConfigPasswordError) as exc_info:
        create_app(get_test_config("no_password"))

    assert isinstance(exc_info.type, type(config.ConfigPasswordError)), "App did not exit on config validation failure."


def test_config_file_creation(allowlistapp: any, get_test_config: dict, caplog: pytest.LogCaptureFixture):
    """Tests relating to config file."""
    # TEST: that file is created when no config is provided.
    with caplog.at_level(logging.WARNING):
        allowlistapp.create_app(
            test_config=get_test_config("testing_true_valid"), instance_path=pytest.TEST_INSTANCE_PATH
        )
        assert "No configuration file found, creating at default location:" in caplog.text


def test_config_file_loading(allowlistapp: any, caplog: pytest.LogCaptureFixture):
    """Tests relating to config file."""
    shutil.copy(os.path.join(pytest.TEST_CONFIGS_LOCATION, "testing_true_valid.toml"), pytest.TEST_CONFIG_FILE_PATH)

    # TEST: that file is created when no config is provided.
    with caplog.at_level(logging.INFO):
        allowlistapp.create_app(test_config=None, instance_path=pytest.TEST_INSTANCE_PATH)
        assert "Using this path as it's the first one that was found" in caplog.text
