"""Unit testing for the config module."""

import os

import pytest
import pytest_mock

from allowlistapp.config import AllowListAppConfig, AppConfig, AuthConfig, FlaskConfig, LoggingConfig, ServicesConfig


def test_config_permissions_error_read(tmp_path, place_test_config, mocker: pytest_mock.plugin.MockerFixture):
    """Mock a Permissions error with mock_open."""
    place_test_config("valid_testing_true.toml", tmp_path)

    mock_open_func = mocker.mock_open(read_data="")
    mock_open_func.side_effect = PermissionError("Permission denied")

    mocker.patch("builtins.open", mock_open_func)

    # TEST: PermissionsError is raised.
    with pytest.raises(PermissionError):
        AllowListAppConfig.load(instance_path=tmp_path)


def test_config_permissions_error_write(tmp_path, place_test_config, mocker: pytest_mock.plugin.MockerFixture):
    """Mock a Permissions error with mock_open."""
    place_test_config("valid_testing_true.toml", tmp_path)

    conf = AllowListAppConfig.load(instance_path=tmp_path)

    mock_open_func = mocker.mock_open(read_data="")
    mock_open_func.side_effect = PermissionError("Permission denied")

    mocker.patch("builtins.open", mock_open_func)

    # TEST: PermissionsError is raised.
    with pytest.raises(PermissionError):
        conf.write_config(os.path.join(tmp_path, "config.toml"))


def test_config_attribute_access(tmp_path, place_test_config):
    """Test that config fields are accessible as typed attributes."""
    place_test_config("valid_testing_true.toml", tmp_path)

    conf = AllowListAppConfig.load(instance_path=tmp_path)

    # TEST: fields are accessible as typed Pydantic model instances.
    assert isinstance(conf.app, AppConfig), "conf.app should be an AppConfig"
    assert isinstance(conf.logging, LoggingConfig), "conf.logging should be a LoggingConfig"
    assert isinstance(conf.flask, FlaskConfig), "conf.flask should be a FlaskConfig"
    assert isinstance(conf.auth, AuthConfig), "conf.auth should be an AuthConfig"
    assert isinstance(conf.services, ServicesConfig), "conf.services should be a ServicesConfig"

    # TEST: model_dump() returns nested dicts suitable for Flask config.
    dumped = conf.model_dump()
    assert isinstance(dumped["app"], dict)
    assert isinstance(dumped["logging"], dict)
    assert isinstance(dumped["flask"], dict)


def test_config_defaults_filled(tmp_path, place_test_config):
    """Test that partial configs are filled in with defaults."""
    place_test_config("valid_testing_true.toml", tmp_path)

    conf = AllowListAppConfig.load(instance_path=tmp_path)

    # TEST: Fields missing from the TOML are populated with defaults.
    assert isinstance(conf.logging.path, str)
    assert isinstance(conf.logging.level, str)
    assert isinstance(conf.app.revert_daily, bool)
    assert isinstance(conf.services.nginx.enabled, bool)
    assert isinstance(conf.app.allowed_subnets, list)


def test_config_extra_keys_ignored(tmp_path, place_test_config):
    """Test that unknown keys in config are silently ignored (extra='ignore')."""
    place_test_config("valid_testing_true.toml", tmp_path)

    # TEST: Extra keys do not raise a validation error.
    conf = AllowListAppConfig(unknown_key="value", app={"auth_type": "static", "db_path": str(tmp_path)})
    assert not hasattr(conf, "unknown_key")
    assert isinstance(conf.app, AppConfig)


def test_config_write_and_load_file(tmp_path, place_test_config):
    """Test write_config and _load_file round-trip."""
    place_test_config("valid_testing_true.toml", tmp_path)

    conf = AllowListAppConfig.load(instance_path=tmp_path)
    config_path = os.path.join(tmp_path, "config.toml")

    # TEST: write_config should not raise.
    conf.write_config(config_path)

    # TEST: _load_file returns a valid dict with expected keys.
    loaded = AllowListAppConfig._load_file(config_path)
    assert isinstance(loaded, dict)
    assert "app" in loaded
    assert "logging" in loaded
