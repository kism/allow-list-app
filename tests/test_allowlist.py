"""Tests the allowlist, its csv database and the nginx writer."""

import logging
from typing import TYPE_CHECKING

import pytest

from allowlistapp.services.allowlist import AllowList, normalise_ip
from allowlistapp.services.nginx import NGINXAllowlist

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_subprocess import FakeProcess

RELOAD = ["sudo", "systemctl", "reload", "nginx"]


def test_default_subnets(tmp_path: Path) -> None:
    """TEST: Allowed subnets are added, IPs inside them match, duplicates aren't added."""
    al = AllowList(tmp_path / "database.csv", ["192.168.0.0/24"], revert_daily=False)

    assert al.is_in_allowlist("192.168.0.55")
    assert not al.is_in_allowlist("10.0.0.1")
    assert not al.add_to_allowlist("bob", "192.168.0.55")
    assert al.add_to_allowlist("bob", "10.0.0.1")


def test_db_loading_valid(tmp_path: Path) -> None:
    """TEST: An existing database is loaded."""
    db_path = tmp_path / "database.csv"
    db_path.write_text("username,ip,date\ntestuser,127.0.0.1,hello\n")

    assert AllowList(db_path, [], revert_daily=False).is_in_allowlist("127.0.0.1")


def test_db_loading_invalid(tmp_path: Path) -> None:
    """TEST: A database with the wrong number of columns fails to load."""
    db_path = tmp_path / "database.csv"
    db_path.write_text("username,ip,date\na,b,c,d,e\n")

    with pytest.raises(ValueError, match="csv not three columns"):
        AllowList(db_path, [], revert_daily=False)


@pytest.mark.parametrize(("returncode", "log_text"), [(0, "Nginx reloaded"), (1, "Couldn't restart nginx")])
def test_nginx_write_and_reload(
    tmp_path: Path, fp: FakeProcess, caplog: pytest.LogCaptureFixture, returncode: int, log_text: str
) -> None:
    """TEST: The nginx allowlist is written and nginx reloaded, a failed reload is logged not raised."""
    fp.register(RELOAD, returncode=returncode)
    fp.keep_last_process(True)  # Written on the subnet add and again on startup
    conf_path = tmp_path / "ipallowlist.conf"

    nginx = NGINXAllowlist(conf_path)
    nginx.reload_nginx_command = RELOAD  # Tests may run as root
    with caplog.at_level(logging.INFO):
        AllowList(tmp_path / "database.csv", ["10.0.0.0/8"], revert_daily=False, nginx_allowlist=nginx)

    assert conf_path.read_text().startswith("allow 10.0.0.0/8; # default, ")
    assert conf_path.read_text().endswith("deny all;")
    assert log_text in caplog.text


def test_nginx_write_bad_path(tmp_path: Path) -> None:
    """TEST: A missing directory for the nginx allowlist raises."""
    with pytest.raises(FileNotFoundError, match="Could not write NGINX allowlist"):
        NGINXAllowlist(tmp_path / "nope" / "ipallowlist.conf").write([])


class StopLoopError(Exception):
    """Break out of the revert loop."""


def test_revert_daily(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """TEST: The revert loop sleeps until 4am first, then clears memory and the database back to the defaults."""
    db_path = tmp_path / "database.csv"
    db_path.write_text("username,ip,date\nbob,10.0.0.1,yesterday\n")
    al = AllowList(db_path, ["192.168.0.0/24"], revert_daily=False)
    assert al.is_in_allowlist("10.0.0.1"), "Startup doesn't wipe the database"

    sleeps: list[float] = []

    def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        if len(sleeps) > 1:
            raise StopLoopError

    monkeypatch.setattr("time.sleep", fake_sleep)

    with pytest.raises(StopLoopError):
        al._revert_list_daily()

    assert 0 < sleeps[0] <= 24 * 60 * 60
    assert not al.is_in_allowlist("10.0.0.1")
    assert al.is_in_allowlist("192.168.0.1")
    assert "10.0.0.1" not in db_path.read_text()
    assert "192.168.0.0/24" in db_path.read_text()


def test_revert_rewrites_nginx(tmp_path: Path, fp: FakeProcess) -> None:
    """TEST: A revert rewrites the nginx allowlist too."""
    fp.register(RELOAD)
    fp.keep_last_process(True)
    conf_path = tmp_path / "ipallowlist.conf"
    nginx = NGINXAllowlist(conf_path)
    nginx.reload_nginx_command = RELOAD

    al = AllowList(tmp_path / "database.csv", [], revert_daily=False, nginx_allowlist=nginx)
    al.add_to_allowlist("bob", "10.0.0.1")
    assert "10.0.0.1" in conf_path.read_text()

    al.revert()
    assert conf_path.read_text() == "deny all;"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("10.0.0.1", "10.0.0.1"),
        (" 10.0.0.1 ", "10.0.0.1"),
        ("192.168.1.5/24", "192.168.1.0/24"),  # Host bits dropped
        ("2001:db8::1", "2001:db8::1"),
        ("2001:db8::1/64", "2001:db8::/64"),
    ],
)
def test_normalise_ip(value: str, expected: str) -> None:
    """TEST: IPs and networks are normalised."""
    assert normalise_ip(value) == expected


@pytest.mark.parametrize("value", ["9.9.9.9; allow all", "10.0.0.1, 10.0.0.2", "testclient", "", "fe80::1%eth0"])
def test_normalise_ip_invalid(value: str) -> None:
    """TEST: Anything that isn't a single IP or network is rejected."""
    with pytest.raises(ValueError):  # ruff: ignore[pytest-raises-too-broad] # ipaddress only raises ValueError
        normalise_ip(value)


def test_add_invalid_ip(tmp_path: Path) -> None:
    """TEST: The allowlist refuses an invalid IP, nothing is written."""
    al = AllowList(tmp_path / "database.csv", [], revert_daily=False)
    with pytest.raises(ValueError):  # ruff: ignore[pytest-raises-too-broad] # ipaddress only raises ValueError
        al.add_to_allowlist("bob", "9.9.9.9; allow all")
    assert al.allowlist == []


def test_nginx_injection(tmp_path: Path, fp: FakeProcess) -> None:
    """TEST: Bad rows in the database and newlines in usernames can't add lines to the nginx config."""
    fp.register(RELOAD)
    fp.keep_last_process(True)
    db_path = tmp_path / "database.csv"
    db_path.write_text(
        "username,ip,date\n"
        '"bob\nallow all;",10.0.0.1,d\n'  # Newline in a quoted csv field
        '"eve","9.9.9.9; allow all",d\n'
    )
    conf_path = tmp_path / "ipallowlist.conf"
    nginx = NGINXAllowlist(conf_path)
    nginx.reload_nginx_command = RELOAD

    al = AllowList(db_path, [], revert_daily=False, nginx_allowlist=nginx)
    al.add_to_allowlist("mallory\r\nallow all;", "10.0.0.2")

    lines = conf_path.read_text().splitlines()
    assert lines == [
        "allow 10.0.0.1; # boballow all;, d",
        f"allow 10.0.0.2; # malloryallow all;, {al.allowlist[1]['date']}",
        "deny all;",
    ]
