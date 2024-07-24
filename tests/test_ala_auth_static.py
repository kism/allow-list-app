"""PyTest, Tests the hello API endpoint."""

import csv
import os
from http import HTTPStatus

import pytest
from flask.testing import FlaskClient


def test_auth_static_fail(client: FlaskClient):
    """Test static authentication failure."""
    response = client.post("/authenticate/", data={"username": "", "password": "hunter3"})
    assert response.data == b"nope", "Auth should have failed"
    assert response.status_code == HTTPStatus.FORBIDDEN

    response = client.get("/check_auth/")
    # TEST: /check_auth/ response
    assert response.data == b"nope", "Auth check should have failed"
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.parametrize(
    ("headers", "expected_entry"),
    [
        ({}, "127.0.0.1"),
        ({"X-Forwarded-For": "192.168.0.1"}, "192.168.0.1"),
    ],
)
def test_auth_static_success(tmp_path, headers, expected_entry, client: FlaskClient):
    """Test auth with the static authentication backend."""
    response = client.post("/authenticate/", data={"username": "", "password": "hunter2"}, headers=headers)
    assert response.status_code == HTTPStatus.OK

    response = client.get("/check_auth/", headers=headers)
    assert response.data == b"yep", "Check auth should have said that user is logged in."
    assert response.status_code == HTTPStatus.OK

    with open(os.path.join(tmp_path, "database.csv")) as f:
        csv_reader = csv.DictReader(f, quoting=csv.QUOTE_MINIMAL)
        allowlist = list(csv_reader).copy()

    # TEST: The resulting database is correct
    assert len(allowlist) == 1
    assert allowlist[0]["ip"] == expected_entry
    assert allowlist[0]["username"] == ""
