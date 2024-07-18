"""Test the logger of the app."""

import logging
import os

import pytest
import pytest_mock


def test_logging_permissions_error(tmp_path, mocker: pytest_mock.plugin.MockerFixture):
    """Try mock a permission error."""
    from allowlistapp.logger import _add_file_handler

    mock_open_func = mocker.mock_open(read_data="")
    mock_open_func.side_effect = PermissionError("Permission denied")

    mocker.patch("builtins.open", mock_open_func)

    logger = logging.getLogger("TEST_LOGGER")

    # TEST: That a permissions error is raised.
    with pytest.raises(PermissionError):
        _add_file_handler(logger, os.path.join(tmp_path, "test.log"))


def test_config_logging_to_dir(tmp_path):
    """Test if logging to directory raises error.

    This one needs to go at the end since it interferes with other tests???
    """
    from allowlistapp.logger import _add_file_handler

    logger = logging.getLogger("TEST_LOGGER")

    # TEST: Check that correct exception is caught when you try log to a folder
    with pytest.raises(IsADirectoryError):
        _add_file_handler(logger, tmp_path)


@pytest.mark.parametrize(
    ("log_level_in", "log_level_expected"),
    [
        (50, 50),
        ("INFO", 20),
        ("WARNING", 30),
        ("INVALID", 20),
    ],
)
def test_set_log_level(log_level_in: str | int, log_level_expected: int):
    """Test if logging to directory raises error.

    This one needs to go at the end since it interferes with other tests???
    """
    from allowlistapp.logger import _set_log_level

    logger = logging.getLogger("TEST_LOGGER")

    # TEST: Logger ends up with correct values
    _set_log_level(logger, log_level_in)
    assert logger.getEffectiveLevel() == log_level_expected

    # Reset the logging object
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()
