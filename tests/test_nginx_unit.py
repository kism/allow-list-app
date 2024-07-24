"""Unit test ngnix reloading."""

import logging
import time
import os
import threading


import pytest

from allowlistapp.al_handler_nginx import NGINXAllowlist


def mock_finish_write(nginx_allowlist):
    time.sleep(1)
    nginx_allowlist._writing = False


def mock_finish_reload(nginx_allowlist):
    time.sleep(1)
    nginx_allowlist._nginx_reloading = False


def test_conflicting_writes(tmp_path):
    """TKTKTKTKTKTKT."""

    ala_conf = {"app": {"allowlist_path": os.path.join(tmp_path, "allowlist.conf")}}
    allowlist = {"date": "1970-01-01", "ip": "127.0.0.1", "username": "TESTUSER"}

    nginx_allowlist = NGINXAllowlist()

    nginx_allowlist._writing = True

    thread = threading.Thread(target=mock_finish_write, args=(nginx_allowlist,))
    thread.start()

    nginx_allowlist.write(ala_conf, allowlist)

    thread.join()

    with open(os.path.join(tmp_path, "allowlist.conf")) as f:
        nginx_conf = f.read()

    assert allowlist["ip"] in nginx_conf


def test_conflicting_reloads(tmp_path):
    """TKTKTKTKTKTKT."""
    nginx_allowlist = NGINXAllowlist()

    nginx_allowlist._nginx_reloading = True

    thread = threading.Thread(target=mock_finish_reload, args=(nginx_allowlist,))
    thread.start()

    nginx_allowlist._reload()

    thread.join()
