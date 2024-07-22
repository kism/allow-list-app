"""Test launching the app and config."""

import logging
import os

import pytest

from allowlistapp import create_app

TEST_DBS_DIR = os.path.join(os.getcwd(), "tests", "db")


def test_db_loading_valid(tmp_path, get_test_config, caplog: pytest.LogCaptureFixture):
    """Tests relating to config file."""
    # TEST: that file is created when no config is provided.

    with caplog.at_level(logging.INFO):
        create_app(test_config=(get_test_config("testing_true_valid.toml")), instance_path=tmp_path)
        assert os.path.exists(os.path.join(tmp_path, "database.csv"))
