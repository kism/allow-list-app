"""Test the logger of the app."""

import contextlib
import logging
import os
from types import FunctionType

import pytest
from flask import Flask


def test_config_invalid_log_level(allowlistapp: any, get_test_config: FunctionType, caplog: pytest.LogCaptureFixture):
    """Test if logging to file works."""
    with caplog.at_level(logging.WARNING):
        app = allowlistapp.create_app(get_test_config("logging_invalid_log_level"))
        # TEST: App still starts
        assert app
        # TEST: Assert that the invalid logging level message gets logged
        assert "Invalid logging level" in caplog.text


def test_handlers_added(allowlistapp: any, app: Flask):
    """Test passing config to app."""
    # TEST: Assert that the config dictionary can set config attributes successfully.
    import allowlistapp.logger

    logger = logging.getLogger("TEST_LOGGER")
    logging_conf = {"path": "", "level": "INFO"}

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

    logging_conf = {"path": pytest.TEST_LOG_PATH, "level": "INFO"}  # Test file handler

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

    os.unlink(pytest.TEST_LOG_PATH)
