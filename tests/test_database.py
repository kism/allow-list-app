"""Test launching the app and config."""

import logging
import os

import pytest

from allowlistapp import create_app

TEST_DBS_DIR = os.path.join(os.getcwd(), "tests", "db")


def test_db_new_valid(tmp_path, get_test_config, caplog: pytest.LogCaptureFixture):
    """Tests relating to config file."""
    # TEST: that file is created when no config is provided.

    create_app(test_config=(get_test_config("valid_testing_true.toml")), instance_path=tmp_path)
    assert os.path.exists(os.path.join(tmp_path, "database.csv"))

    with caplog.at_level(logging.WARNING):
        assert "No database found, will be created the first time a IP is added" in caplog.text


def test_db_loading_valid(get_test_config, tmp_path, caplog: pytest.LogCaptureFixture):
    """Tests relating to config file."""
    with open(os.path.join(TEST_DBS_DIR, "valid.csv")) as f:
        db_contents = f.read()

    tmp_f = tmp_path / "database.csv"

    tmp_f.write_text(db_contents)

    create_app(test_config=get_test_config("valid_no_revert_daily.toml"), instance_path=tmp_path)

    # TEST: Valid database loads.
    with caplog.at_level(logging.INFO):
        assert "Database found at" in caplog.text
        assert "Database checks passed" in caplog.text


def test_db_loading_invalid(get_test_config, tmp_path, caplog: pytest.LogCaptureFixture):
    """Tests relating to config file."""
    with open(os.path.join(TEST_DBS_DIR, "invalid.csv")) as f:
        db_contents = f.read()

    tmp_f = tmp_path / "database.csv"

    tmp_f.write_text(db_contents)

    # TEST: Valid database fails to load.
    with pytest.raises(ValueError, match="csv not three columns"):
        create_app(test_config=get_test_config("valid_no_revert_daily.toml"), instance_path=tmp_path)

    with caplog.at_level(logging.INFO):
        assert "Database found at" in caplog.text

    with caplog.at_level(logging.CRITICAL):
        assert "of csv not three columns" in caplog.text
