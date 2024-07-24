"""PyTest, Tests the hello API endpoint."""

from http import HTTPStatus

import pytest
from flask.testing import FlaskClient


def test_auth_static_fail(client: FlaskClient):
    """TKTKTKTKTKKTKT."""
    response = client.post("/authenticate/", data={"username": "", "password": "hunter3"})
    assert response.data == b"nope", "Auth should have failed"
    assert response.status_code == HTTPStatus.FORBIDDEN

    response = client.get("/check_auth/")
    # TEST: /check_auth/ response
    assert response.data == b"nope", "Auth check should have failed"
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.parametrize(
    ("headers"),
    [
        ({}),
        ({"X-Forwarded-For": "192.168.0.1"}),
    ],
)
def test_auth_static_success(headers, client: FlaskClient):
    """TKTKTKTKTKKTKT."""
    response = client.post("/authenticate/", data={"username": "", "password": "hunter2"}, headers=headers)
    assert response.status_code == HTTPStatus.OK

    response = client.get("/check_auth/", headers=headers)
    assert response.data == b"yep", "Check auth should have said that user is logged in."
    assert response.status_code == HTTPStatus.OK
