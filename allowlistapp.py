#!/usr/bin/env python3
"""Flask webapp to control a nginx allowlist"""

import argparse
import logging
import os
import json
import subprocess
import threading
import time
import pwd

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from flask import Flask, render_template, request  # , jsonify

ph = PasswordHasher()
app = Flask(__name__)  # Flask app object
args = None
settings = None
reload_nginx_pending = False


@app.route("/")
def home():
    """Flask Home"""
    return render_template("home.html.j2")


@app.route("/authenticate/", methods=["POST"])
def my_form_post():
    """Post da password"""
    global reload_nginx_pending

    text = request.form["password"]
    result = check_password(text)
    out_text = "Validation Failed"
    status = 403

    # Get IP
    if request.environ.get("HTTP_X_FORWARDED_FOR") is None:
        ip = request.environ["REMOTE_ADDR"]
    else:
        ip = request.environ["HTTP_X_FORWARDED_FOR"]

    if result:
        status = 200
        out_text = "Success!"
        write_allowlist_file(ip)
        reload_nginx_pending = True

    print(ip + " " + out_text)
    return render_template("result.html.j2", out_text=out_text, status=status)


def write_allowlist_file(ip):
    """Write to the nginx allowlist conf file"""

    with open(settings["path_to_allowlist"], "r", encoding="utf8") as conf_file:
        content = conf_file.read()

    with open(settings["path_to_allowlist"], "w", encoding="utf8") as conf_file:
        content = "Allow " + ip + ";\n" + content
        content = check_allowlist(content)
        # print("Content to write: \n" + content)
        conf_file.write(content)


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


def process_password(in_settings):
    """Hash Password"""
    # Hash password if there is a plaintext password set
    if settings["plaintext_password"] != "":
        print("Plaintext password set, hashing and removing from config file")
        plaintext = settings["plaintext_password"]
        hashed = ph.hash(plaintext)
        settings["hashed_password"] = hashed
        settings["plaintext_password"] = ""
    else:
        print("Found hashed password")

    return in_settings


def check_allowlist(conf):
    """Validate the list"""
    errors_occurred = False

    lines = conf.splitlines()
    lines.append("deny all;")
    lines = list(set(lines))
    lines.sort()

    # print("Lines: \n" + str(lines))

    for line in lines:
        words = line.lower().split()
        if words[0] not in ["allow", "deny"]:
            print("First word in line isn't allow or deny")
            errors_occurred = True

        if line[-1] != ";":
            print("No ';' at end of line")
            errors_occurred = True

        if len(words) != 2:
            print("Word count validation failed for line: " + line)
            errors_occurred = True

    conf = "\n".join(lines)

    if errors_occurred:
        conf = "deny all;"

    return conf


def reload_nginx():
    """Reload nginx"""
    global reload_nginx_pending
    user_account = pwd.getpwuid(os.getuid())[0]

    reload_nginx_command = ["systemctl", "reload", "nginx"]
    if user_account != "root":
        reload_nginx_command = ["sudo", "systemctl", "reload", "nginx"]

    while True:
        time.sleep(1)
        if reload_nginx_pending:
            print("Reloading nginx")
            time.sleep(1)
            try:
                subprocess.run(reload_nginx_command, check=True)
            except subprocess.CalledProcessError:
                print("Couldnt restart nginx, either: ")
                print("Nginx isnt installed")
                print("or")
                print("Sudoers rule not created for this user (" + user_account + ")")
                print("Create and edit a sudoers file")
                print(" visudo /etc/sudoers.d/" + user_account)
                print("And insert the text:")
                print(
                    " "
                    + user_account
                    + " ALL=(root) NOPASSWD: /usr/sbin/systemctl reload nginx"
                )

            reload_nginx_pending = False


def main():
    """Start Flask webapp"""

    if not os.path.exists(settings["path_to_allowlist"]): # Create if file doesn't exist
        with open(settings["path_to_allowlist"], "w", encoding="utf8") as conf_file:
            conf_file.write("deny all;")

    # Start thread: restart handler
    thread = threading.Thread(target=reload_nginx, daemon=True)
    thread.start()

    app.run(host=args.WEBADDRESS, port=args.WEBPORT)

    # Cleanup
    thread.join()


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
        default="settings.json",
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
    errors_loading = False
    if not os.path.exists(args.settingspath):
        errors_loading = True
        with open(args.settingspath, "w", encoding="utf8") as json_file:
            settings = {
                "path_to_allowlist": "ipallowist.conf",
                "plaintext_password": "",
                "hashed_password": "",
            }
            json.dump(
                settings, json_file, indent=2
            )  # indent parameter is optional for pretty formatting
        print("No config file found, creating default")
    else:
        with open(args.settingspath, "r", encoding="utf8") as json_file:
            settings = json.load(json_file)

        settings = process_password(settings)

        with open(args.settingspath, "w", encoding="utf8") as json_file:
            json.dump(
                settings, json_file, indent=2
            )  # indent parameter is optional for pretty formatting

    if not errors_loading:
        if settings["plaintext_password"] == "" and settings["hashed_password"] == "":
            errors_loading = True
            print("Please set password in: " + args.settingspath)

    if not errors_loading:
        main()

    print("Exiting")
