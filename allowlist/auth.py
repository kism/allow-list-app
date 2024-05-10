#!/usr/bin/env python3
"""Flask webapp to control a nginx allowlist"""

import logging

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from flask import Blueprint, render_template, request, current_app

from . import allowlist
from . import get_app_settings

# from .settings import get_settings

bp = Blueprint("auth", __name__)
ph = PasswordHasher()

app_settings = get_app_settings()

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
        allowlist.write_allowlist_file(app_settings, ip)

    logging.info("%s: %s", out_text, ip)
    return render_template("result.html.j2", out_text=out_text, status=status)


def check_password(text):
    """Check password (secure) (I hope)"""
    passwordcorrect = False
    hashed = current_app.config["hashed_password"]
    try:
        ph.verify(hashed, text)
        passwordcorrect = True
    except VerifyMismatchError:
        pass

    return passwordcorrect


def process_password():
    """Hash Password"""
    # Hash password if there is a plaintext password set
    if current_app.config["plaintext_password"] != "":
        logging.info("Plaintext password set, hashing and removing from config file")
        plaintext = current_app.config["plaintext_password"]
        hashed = ph.hash(plaintext)
        current_app.config["hashed_password"] = hashed
        current_app.config["plaintext_password"] = ""
    elif current_app.config["hashed_password"] == "":
        logging.error("❌ No hashed password")
    else:
        logging.info("Found hashed password, probably")

