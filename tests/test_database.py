"""Test launching the app and config."""

import logging
import os

import pytest

from allowlistapp import create_app

TEST_DBS_DIR = os.path.join(os.getcwd(), "tests", "db")


def test_db_loading_valid(tmp_path, get_test_config, caplog: pytest.LogCaptureFixture):
    """Tests relating to config file."""
    # TEST: that file is created when no config is provided.

    assert not os.path.exists(os.path.join(os.getcwd(), "test.csv")), "HERHEHRHEHRE"

    with caplog.at_level(logging.INFO):
        create_app(test_config=(get_test_config("testing_true_valid")), instance_path=tmp_path)
        assert "Database checks passed" in caplog.text

    assert not os.path.exists(os.path.join(os.getcwd(), "test.csv")), "HERHEHRHEHRE____AFTER"
