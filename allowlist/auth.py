"""Flask webapp to control a nginx allowlist."""

import json
import logging

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from flask import Blueprint, request

from . import allowlist_handler, get_ala_settings

bp = Blueprint("auth", __name__)
ph = PasswordHasher()
ala_settings = get_ala_settings()
al = allowlist_handler.AllowList(ala_settings)
logger = logging.getLogger("allowlist")

if not ala_settings.auth_type_static():
    from http import HTTPStatus

    import requests

dynamic_auth_types = {
    "jellyfin": {
        "endpoint": "Users/authenticatebyname",
        "username_field": "Username",
        "password_field": "Pw",
        "headers": {
            "Authorization": (
                'MediaBrowser Client="Allowlist App", '
                'Device="Python Flask", '
                'DeviceId="lmao", '
                'Version="0.0", '
                'Token="lmao"'
            ),
            "Content-Type": "application/json",
        },
    },
}


@bp.route("/checkauth/", methods=["GET"])
def check_auth() -> int:
    """Test Authenticate."""
    if request.environ.get("HTTP_X_FORWARDED_FOR") is None:
        ip = request.environ["REMOTE_ADDR"]
    else:
        ip = request.environ["HTTP_X_FORWARDED_FOR"]

    status = 401
    message = "nope"
    if al.is_in_allowlist(ip):
        message = "yep"
        status = 200

    return message, status


@bp.route("/authenticate/", methods=["POST"])
def authenticate() -> str:
    """Post da password."""
    username = request.form["username"]
    password = request.form["password"]

    if ala_settings.auth_type_static():
        result = check_password_static(password)
    else:
        result = check_password_url(username, password)

    message = "nope"
    status = 401

    if result:
        status = 200
        message = "yep"

    # Get IP
    if request.environ.get("HTTP_X_FORWARDED_FOR") is None:
        ip = request.environ["REMOTE_ADDR"]
    else:
        ip = request.environ["HTTP_X_FORWARDED_FOR"]

    username_text = ""
    if username != "":
        username_text = f", Username: {username}"

    logger.info("Authentication returned: %s for %s%s", message, ip, username_text)

    if result:
        al.add_to_allowlist(username, ip)

    return message, status


def check_password_static(password: str) -> bool:
    """Check password (secure) (I hope)."""
    passwordcorrect = False
    hashed = ala_settings.static_password_hashed
    try:
        ph.verify(hashed, password)
        passwordcorrect = True
    except VerifyMismatchError:
        pass

    return passwordcorrect


def check_password_url(username: str, password: str) -> bool:
    """Check password via Jellyfin (secure) (I hope)."""
    passwordcorrect = False

    url = ala_settings.remote_auth_url + "/" + dynamic_auth_types[ala_settings.auth_type]["endpoint"]
    headers = dynamic_auth_types[ala_settings.auth_type]["headers"]

    data = {
        dynamic_auth_types[ala_settings.auth_type]["username_field"]: username,
        dynamic_auth_types[ala_settings.auth_type]["password_field"]: password,
    }
    json_data = json.dumps(data)

    response = None
    try:
        response = requests.post(url, headers=headers, data=json_data, timeout=5)
    except requests.exceptions.ConnectionError:
        logger.error("Connection error for url: %s", url)  # noqa: TRY400 # We dont need to treat this as an exception
    except requests.exceptions.Timeout:
        logger.error("Timeout exception for url: %s", url)  # noqa: TRY400 # We dont need to treat this as an exception
    except Exception:
        logger.exception("Uncaught exception for url: %s", url)

    if response and response.status_code == HTTPStatus.OK:
        passwordcorrect = True

    return passwordcorrect
