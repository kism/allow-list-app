"""Unit test ngnix reloading."""

import logging
import os
import threading
import time

import pytest

from allowlistapp import al_handler_nginx


def mock_finish_write(nginx_allowlist):
    """This mocks an allowlist which is currently writing, thus we need to wait for it to finish."""
    time.sleep(0.5)
    nginx_allowlist._writing = False


def mock_finish_reload(nginx_allowlist):
    """This mocks an allowlist which is currently reloading, thus we need to wait for it to finish."""
    time.sleep(0.5)
    nginx_allowlist._nginx_reloading = False


def test_conflicting_writes(tmp_path, fp, caplog):
    """Test writing the allowlist when the object has a pending write."""
    fp.register(["sudo", "systemctl", "reload", "nginx"], returncode=0)

    al_handler_nginx.logger.setLevel(logging.DEBUG)

    ala_conf = {
        "services": {
            "nginx": {"allowlist_path": os.path.join(tmp_path, "ipallowlist.conf")},
        },
    }
    allowlist = [
        {"date": "1970-01-01", "ip": "127.0.0.1", "username": "TESTUSER"},
        {"date": "2023-01-01", "ip": "192.168.0.1", "username": "TESTUSER2"},
        {"date": "2024-01-01", "ip": "192.168.0.2", "username": "TESTUSER3"},
    ]

    nginx_allowlist = al_handler_nginx.NGINXAllowlist()

    nginx_allowlist._writing = True

    thread = threading.Thread(target=mock_finish_write, args=(nginx_allowlist,))
    thread.start()

    nginx_allowlist.write(ala_conf, allowlist)

    thread.join()

    with caplog.at_level(logging.DEBUG):
        assert "Finished writing nginx allowlist" in caplog.text

    with open(os.path.join(tmp_path, "ipallowlist.conf")) as f:
        nginx_conf = f.read()

    for item in allowlist:
        assert item["date"] in nginx_conf
        assert item["username"] in nginx_conf
        assert item["ip"] in nginx_conf


def test_conflicting_reloads():
    """Test reloading the object has a pending reload."""
    nginx_allowlist = al_handler_nginx.NGINXAllowlist()

    nginx_allowlist._nginx_reloading = True

    thread = threading.Thread(target=mock_finish_reload, args=(nginx_allowlist,))
    thread.start()

    nginx_allowlist._reload()

    thread.join()


@pytest.mark.parametrize(
    ("path", "expected_log"),
    [
        ("", "In the config, please enter a path for the NGINX allowlist file."),
        ("PATH/THAT/DOES/NOT/EXIST", "Could not write NGINX allowlist file to path: PATH/THAT/DOES/NOT/EXIST"),
    ],
)
def test_invalid_allowlist_path(path, expected_log, fp, caplog):
    """Test writing the allowlist when the object has a pending write."""
    al_handler_nginx.logger.setLevel(logging.DEBUG)

    ala_conf = {
        "services": {
            "nginx": {"allowlist_path": path},
        },
    }
    allowlist = []

    nginx_allowlist = al_handler_nginx.NGINXAllowlist()

    with pytest.raises(FileNotFoundError):
        nginx_allowlist.write(ala_conf, allowlist)

    with caplog.at_level(logging.CRITICAL):
        assert expected_log in caplog.text
