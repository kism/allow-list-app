#!/usr/bin/env python3
"""Flask webapp to control a nginx allowlist"""

import logging

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from flask import Blueprint, render_template, request

from . import allowlist
from . import get_ala_settings

# from .settings import get_settings

bp = Blueprint("auth", __name__)
ph = PasswordHasher()

ala_settings = get_ala_settings()


@bp.route("/authenticate/", methods=["POST"])
def my_form_post():
    """Post da password"""

    text = request.form["password"]
    result = check_password(text)
    out_text = "Validation Failed"
    status = 403

    # Get IP
    if request.environ.get("HTTP_X_FORWARDED_FOR") is None:
        ip = request.environ["REMOTE_ADDR"]
    else:
        ip = request.environ["HTTP_X_FORWARDED_FOR"]

    # for thing in enumerate(request.environ):
    #     print(thing)

    if result:
        status = 200
        out_text = "Successful Auth!"
        allowlist.write_allowlist_file(ala_settings, ip)

    logging.info("%s: %s", out_text, ip)
    return render_template("result.html.j2", out_text=out_text, status=status)


def check_password(text):
    """Check password (secure) (I hope)"""
    passwordcorrect = False
    hashed = ala_settings.password_hashed
    try:
        ph.verify(hashed, text)
        passwordcorrect = True
    except VerifyMismatchError:
        pass

    return passwordcorrect