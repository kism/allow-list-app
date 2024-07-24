"""Unit test ngnix reloading."""

import logging
import os
import threading
import time

from allowlistapp import al_handler_nginx


def mock_finish_write(nginx_allowlist):
    """This mocks an allowlist which is currently writing, thus we need to wait for it to finish."""
    time.sleep(1)
    nginx_allowlist._writing = False


def mock_finish_reload(nginx_allowlist):
    """This mocks an allowlist which is currently reloading, thus we need to wait for it to finish."""
    time.sleep(1)
    nginx_allowlist._nginx_reloading = False


def test_conflicting_writes(tmp_path, fp, caplog):
    """TKTKTKTKTKTKT."""
    fp.register(["sudo", "systemctl", "reload", "nginx"], returncode=0)

    al_handler_nginx.logger.setLevel(logging.DEBUG)

    ala_conf = {"app": {"allowlist_path": os.path.join(tmp_path, "allowlist.conf")}}
    allowlist = {"date": "1970-01-01", "ip": "127.0.0.1", "username": "TESTUSER"}

    nginx_allowlist = al_handler_nginx.NGINXAllowlist()

    nginx_allowlist._writing = True

    thread = threading.Thread(target=mock_finish_write, args=(nginx_allowlist,))
    thread.start()

    nginx_allowlist.write(ala_conf, allowlist)

    thread.join()

    with caplog.at_level(logging.DEBUG):
        assert "Finished writing nginx allowlist" in caplog.text

    with open(os.path.join(tmp_path, "allowlist.conf")) as f:
        nginx_conf = f.read()

    al_handler_nginx.logger.debug(nginx_conf)
    with caplog.at_level(logging.DEBUG):
        assert allowlist["ip"] in caplog.text

    assert allowlist["ip"] in nginx_conf


def test_conflicting_reloads(tmp_path):
    """TKTKTKTKTKTKT."""
    nginx_allowlist = al_handler_nginx.NGINXAllowlist()

    nginx_allowlist._nginx_reloading = True

    thread = threading.Thread(target=mock_finish_reload, args=(nginx_allowlist,))
    thread.start()

    nginx_allowlist._reload()

    thread.join()
