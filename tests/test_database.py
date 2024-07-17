"""Test launching the app and config."""

import logging
import os
import shutil

import pytest

TEST_DBS_DIR = os.path.join(os.getcwd(), "tests", "db")


def test_db_loading_valid(allowlistapp: any, get_test_config: dict, caplog: pytest.LogCaptureFixture):
    """Tests relating to config file."""
    shutil.copy(os.path.join(TEST_DBS_DIR, "valid.csv"), pytest.TEST_DB_PATH)

    # TEST: that file is created when no config is provided.
    with caplog.at_level(logging.INFO):
        allowlistapp.create_app(
            test_config=(get_test_config("testing_true_valid")), instance_path=pytest.TEST_INSTANCE_PATH
        )
        assert "Database checks passed" in caplog.text
