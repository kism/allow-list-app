"""Unit testing for the config module."""

from collections.abc import Callable
from pathlib import Path

import pytest
import pytest_mock

from allowlistapp.config import AllowListAppConfig, AppConfig, AuthConfig, FlaskConfig, LoggingConfig, ServicesConfig


def test_config_permissions_error_read(
    tmp_path: Path, place_test_config: Callable[[str, Path | str], None], mocker: pytest_mock.plugin.MockerFixture
) -> None:
    """Mock a Permissions error with mock_open."""
    place_test_config("valid_testing_true.toml", tmp_path)

    mocker.patch("pathlib.Path.open", side_effect=PermissionError("Permission denied"))

    # TEST: PermissionsError is raised.
    with pytest.raises(PermissionError):
        AllowListAppConfig.load(instance_path=tmp_path)


def test_config_permissions_error_write(
    tmp_path: Path, place_test_config: Callable[[str, Path | str], None], mocker: pytest_mock.plugin.MockerFixture
) -> None:
    """Mock a Permissions error with mock_open."""
    place_test_config("valid_testing_true.toml", tmp_path)

    conf = AllowListAppConfig.load(instance_path=tmp_path)

    mocker.patch("pathlib.Path.open", side_effect=PermissionError("Permission denied"))

    # TEST: PermissionsError is raised.
    with pytest.raises(PermissionError):
        conf.write_config(tmp_path / "config.toml")


def test_config_attribute_access(tmp_path: Path, place_test_config: Callable[[str, Path | str], None]) -> None:
    """Test that config fields are accessible as typed attributes."""
    place_test_config("valid_testing_true.toml", tmp_path)

    conf = AllowListAppConfig.load(instance_path=tmp_path)

    # TEST: fields are accessible as typed Pydantic model instances.
    assert isinstance(conf.app, AppConfig), "conf.app should be an AppConfig"
    assert isinstance(conf.logging, LoggingConfig), "conf.logging should be a LoggingConfig"
    assert isinstance(conf.flask, FlaskConfig), "conf.flask should be a FlaskConfig"
    assert isinstance(conf.auth, AuthConfig), "conf.auth should be an AuthConfig"
    assert isinstance(conf.services, ServicesConfig), "conf.services should be a ServicesConfig"

    # TEST: model_dump() returns nested dicts suitable for TOML serialization.
    dumped = conf.model_dump()
    assert isinstance(dumped["app"], dict)
    assert isinstance(dumped["logging"], dict)
    assert isinstance(dumped["flask"], dict)


def test_config_defaults_filled(tmp_path: Path, place_test_config: Callable[[str, Path | str], None]) -> None:
    """Test that partial configs are filled in with defaults."""
    place_test_config("valid_testing_true.toml", tmp_path)

    conf = AllowListAppConfig.load(instance_path=tmp_path)

    # TEST: Fields missing from the TOML are populated with defaults.
    assert conf.logging.path is None or isinstance(conf.logging.path, Path)
    assert isinstance(conf.logging.level, str)
    assert isinstance(conf.app.revert_daily, bool)
    assert isinstance(conf.services.nginx.enabled, bool)
    assert isinstance(conf.app.allowed_subnets, list)
    # db_path gets set to a real path after post-validation
    assert isinstance(conf.app.db_path, Path)


def test_config_extra_keys_ignored(tmp_path: Path, place_test_config: Callable[[str, Path | str], None]) -> None:
    """Test that unknown keys in config are silently ignored (extra='ignore')."""
    place_test_config("valid_testing_true.toml", tmp_path)

    # TEST: Extra keys do not raise a validation error.
    conf = AllowListAppConfig(unknown_key="value", app=AppConfig(auth_type="static", db_path=tmp_path))  # type: ignore[call-arg]
    assert not hasattr(conf, "unknown_key")
    assert isinstance(conf.app, AppConfig)


def test_config_write_and_load_file(tmp_path: Path, place_test_config: Callable[[str, Path | str], None]) -> None:
    """Test write_config and _load_file round-trip."""
    place_test_config("valid_testing_true.toml", tmp_path)

    conf = AllowListAppConfig.load(instance_path=tmp_path)
    config_path = tmp_path / "config.toml"

    # TEST: write_config should not raise.
    conf.write_config(config_path)

    # TEST: _load_file returns a valid dict with expected keys.
    loaded = AllowListAppConfig._load_file(config_path)
    assert isinstance(loaded, dict)
    assert "app" in loaded
    assert "logging" in loaded
