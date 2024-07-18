"""PyTest, Tests the hello API endpoint."""

from http import HTTPStatus

from flask.testing import FlaskClient


def test_auth_static_fail(client: FlaskClient):
    """Test the hello API endpoint. This one uses the fixture in conftest.py."""
    response = client.post("/authenticate/", data={"username": "", "password": "hunter3"})
    assert response.data == b"nope", "Auth should have failed"
    assert response.status_code == HTTPStatus.FORBIDDEN

    response = client.get("/check_auth/")
    # TEST: /check_auth/ response
    assert response.data == b"nope", "Auth check should have failed"
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_auth_static_success(client: FlaskClient):
    """Test the hello API endpoint. This one uses the fixture in conftest.py."""
    response = client.post("/authenticate/", data={"username": "", "password": "hunter2"})
    assert response.status_code == HTTPStatus.OK

    response = client.get("/check_auth/")
    assert response.data == b"yep", "Check auth should have said that user is logged in."
    assert response.status_code == HTTPStatus.OK
