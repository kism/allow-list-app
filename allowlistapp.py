#!/usr/bin/env python3
"""Flask webapp that interfaces with mGBA with _emulator/gba_grabwebinput.lua"""

# pylint: disable=global-statement

import argparse
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import time
import socket
import threading
import logging
import os
import json

from flask import Flask, render_template, request, jsonify

ph = PasswordHasher()
app = Flask(__name__)  # Flask app object
args = None
settings = None

@app.route("/")
def home():
    """Flask Home"""
    return render_template("home.html.j2")

@app.route('/', methods=['POST'])
def my_form_post():
    """Post da password"""
    text = request.form['text']
    result = check_password(text)
    if result:
        if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
            ip = request.environ['REMOTE_ADDR']
        else:
            ip = request.environ['HTTP_X_FORWARDED_FOR']

        write_allowlist_file(ip)

    return str(result)

def write_allowlist_file(ip):
    allowlistpath = settings["path_to_allowlist"]

    # Settings File
    if not os.path.exists(allowlistpath):
        with open(allowlistpath, 'w') as conf_file:
            conf_file.write("deny all;")

    with open(allowlistpath, 'r+') as conf_file:
        content = conf_file.read()
        conf_file.seek(0, 0)
        conf_file.write("Allow " + ip + ';\n' + content)


    # with open(args.settingspath, 'r') as conf_file:


    # with open(args.settingspath, 'w') as conf_file:



def check_password(text):
    """Check password (secure) (I hope)"""
    passwordcorrect = False
    hashed = settings["hashed_password"]
    try:
        ph.verify(hashed, text)
        passwordcorrect = True
    except VerifyMismatchError:
        pass

    return passwordcorrect



def process_password(settings):
    """Hash Password"""

    # Hash password if there is a plaintext password set
    if settings["plaintext_password"] != "":
        plaintext = settings["plaintext_password"]
        hashed = ph.hash(plaintext)
        settings["hashed_password"] = hashed
        settings["plaintext_password"] = ""

    return settings




def main():
    """Start Flask webapp"""
    app.run(host=args.WEBADDRESS, port=args.WEBPORT)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flask WebUI, Socket Sender for mGBA")
    parser.add_argument(
        "-wa",
        "--webaddress",
        type=str,
        dest="WEBADDRESS",
        help="(WebUI) Web address to listen on, default is 0.0.0.0",
        default="0.0.0.0",
    )
    parser.add_argument(
        "-wp",
        "--webport",
        type=int,
        dest="WEBPORT",
        help="(WebUI) Web port to listen on, default is 5000",
        default=5000,
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        dest="settingspath",
        help="Config path /path/to/settings.json",
        default="settings.json"
    )
    parser.add_argument(
        "--debug", dest="debug", action="store_true", help="Show debug output"
    )
    args = parser.parse_args()

    # Flask Logger
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)
    if args.debug:
        log.setLevel(logging.DEBUG)

    # Settings File
    if not os.path.exists(args.settingspath):
        raise FileNotFoundError(f"The file '{args.settingspath}' does not exist.")

    with open(args.settingspath, 'r') as json_file:
        settings = json.load(json_file)

    settings = process_password(settings)

    with open(args.settingspath, 'w') as json_file:
        json.dump(settings, json_file, indent=2)  # indent parameter is optional for pretty formatting


    main()
