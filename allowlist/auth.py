"""Flask webapp to control a nginx allowlist."""

import logging

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from flask import Blueprint, render_template, request

from . import allowlist, get_ala_settings

bp = Blueprint("auth", __name__)
ph = PasswordHasher()

ala_settings = get_ala_settings()
logger = logging.getLogger("allowlist")


@bp.route("/authenticate/", methods=["POST"])
def my_form_post() -> str:
    """Post da password."""
    text = request.form["password"]
    result = check_password(text)
    out_text = "Validation Failed"
    status = 403

    # Get IP
    if request.environ.get("HTTP_X_FORWARDED_FOR") is None:
        ip = request.environ["REMOTE_ADDR"]
    else:
        ip = request.environ["HTTP_X_FORWARDED_FOR"]

    logger.info("%s: %s", out_text, ip)
    if result:
        status = 200
        allowlist.write_allowlist_file(ala_settings, ip)

    return render_template("result.html.j2", out_text=out_text, status=status)


def check_password(text: str) -> bool:
    """Check password (secure) (I hope)."""
    passwordcorrect = False
    hashed = ala_settings.password_hashed
    try:
        ph.verify(hashed, text)
        passwordcorrect = True
    except VerifyMismatchError:
        pass

    return passwordcorrect
