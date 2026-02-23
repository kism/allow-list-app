"""Test the logger of the app."""

import logging
from pathlib import Path
from types import FunctionType

import pytest
from flask import Flask

import allowlistapp.logger
from allowlistapp import create_app
from allowlistapp.config import LoggingConfig


def test_config_invalid_log_level(tmp_path: Path, get_test_config: FunctionType, caplog: pytest.LogCaptureFixture) -> None:
    """Test if logging to file works."""
    with caplog.at_level(logging.WARNING):
        create_app(get_test_config("invalid_log_level.toml"), instance_path=tmp_path)

    # TEST: Assert that the invalid logging level message gets logged
    assert "Invalid logging level" in caplog.text


def test_handlers_added(tmp_path: Path, app: Flask) -> None:
    """Test passing config to app."""
    # TEST: Assert that the config dictionary can set config attributes successfully.

    logger = logging.getLogger("TEST_LOGGER")
    logging_conf = LoggingConfig(level="INFO")

    # TEST: Only one handler (console), should exist when no logging path provided
    allowlistapp.logger.setup_logger(app, logging_conf, logger)
    assert len(logger.handlers) == 1

    # TEST: If a console handler exists, another one shouldn't be created
    allowlistapp.logger.setup_logger(app, logging_conf, logger)
    assert len(logger.handlers) == 1

    # Reset the object
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()

    assert len(logger.handlers) == 0  # Check the object reset worked

    logging_conf = LoggingConfig(level="INFO", path=tmp_path / "test.log")  # Test file handler

    # TEST: Two handlers when logging to file expected
    allowlistapp.logger.setup_logger(app, logging_conf, logger)
    assert len(logger.handlers) == 2  # noqa: PLR2004 A console and a file handler are expected

    # TEST: Two handlers when logging to file expected, another one shouldn't be created
    allowlistapp.logger.setup_logger(app, logging_conf, logger)
    assert len(logger.handlers) == 2  # noqa: PLR2004 A console and a file handler are expected

    # Reset the object
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()
