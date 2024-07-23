"""Test launching the app and config."""

import logging
import os

import pytest

from allowlistapp import config, create_app


def test_config_valid(tmp_path, get_test_config):
    """Test passing config to app."""
    # TEST: Assert that the config dictionary can set config attributes successfully.
    assert not create_app(
        get_test_config("valid_testing_false.toml"), instance_path=tmp_path
    ).testing, "Flask testing config item not being set correctly."
    assert create_app(
        get_test_config("valid_testing_true.toml"), instance_path=tmp_path
    ).testing, "Flask testing config item not being set correctly."


def test_config_static_invalid(tmp_path, get_test_config):
    """Test that program exits when given invalid config."""
    # TEST: Assert that the program exists when provided an invalid config dictionary.
    with pytest.raises(config.ConfigPasswordError) as exc_info:
        create_app(get_test_config("invalid_static_auth_no_password.toml"), instance_path=tmp_path)

    assert isinstance(exc_info.type, type(config.ConfigPasswordError)), "App did not exit on config validation failure."


def test_config_invalid_auth_url(tmp_path, get_test_config):
    """Test that program exits when given invalid config."""
    # TEST: Assert that the program exists when provided an invalid config dictionary.
    with pytest.raises(config.ConfigUrlAuthError) as exc_info:
        create_app(get_test_config("invalid_url_auth_url.toml"), instance_path=tmp_path)

    assert isinstance(exc_info.type, type(config.ConfigUrlAuthError)), "App did not exit on config validation failure."


def test_config_invalid_auth_type(tmp_path, get_test_config):
    """Test that program exits when given invalid config."""
    # TEST: Assert that the program exists when provided an invalid config dictionary.
    with pytest.raises(config.ConfigUrlAuthError) as exc_info:
        create_app(get_test_config("invalid_url_auth_type.toml"), instance_path=tmp_path)

    assert isinstance(exc_info.type, type(config.ConfigUrlAuthError)), "App did not exit on config validation failure."


def test_config_valid_hashed_password(tmp_path, get_test_config, caplog):
    """Test that program exits when given invalid config."""
    # TEST: Assert that the program exists when provided an invalid config dictionary.
    create_app(get_test_config("valid_testing_static_auth.toml"), instance_path=tmp_path)

    with caplog.at_level(logging.INFO):
        assert "Found hashed password" in caplog.text


def test_config_file_creation(tmp_path, get_test_config, caplog: pytest.LogCaptureFixture):
    """Tests relating to config file."""
    # TEST: that file is created when no config is provided.
    with caplog.at_level(logging.WARNING):
        create_app(test_config=get_test_config("valid_testing_true.toml"), instance_path=tmp_path)
        assert "No configuration file found, creating at default location:" in caplog.text


def test_config_file_loading(tmp_path, caplog: pytest.LogCaptureFixture):
    """Tests relating to config file."""
    with open(os.path.join(pytest.TEST_CONFIGS_LOCATION, "valid_testing_true.toml")) as f:
        config_contents = f.read()

    tmp_f = tmp_path / "config.toml"

    tmp_f.write_text(config_contents)

    # TEST: that file is created when no config is provided.
    caplog.set_level(logging.INFO)
    create_app(test_config=None, instance_path=tmp_path)
    assert "Using this path as it's the first one that was found" in caplog.text
