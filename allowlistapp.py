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
import ipaddress
import datetime
import sys

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from flask import Flask, render_template, request  # , jsonify
from waitress import serve

ph = PasswordHasher()
app = Flask(__name__)  # Flask app object
args = None
settings = None
reload_nginx_pending = False
LOGLEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


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
        out_text = "Successful Auth!"
        write_allowlist_file(ip)
        reload_nginx_pending = True

    logging.info("%s %s", ip, out_text)
    return render_template("result.html.j2", out_text=out_text, status=status)


def write_allowlist_file(ip):
    """Write to the nginx allowlist conf file"""

    with open(settings["path_to_allowlist"], "r", encoding="utf8") as conf_file:
        content = conf_file.read()

    with open(settings["path_to_allowlist"], "w", encoding="utf8") as conf_file:
        content = "allow " + ip + ";\n" + content
        content = check_allowlist(content)
        # logging.info("Content to write: \n" + content)
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
        logging.info("Plaintext password set, hashing and removing from config file")
        plaintext = settings["plaintext_password"]
        hashed = ph.hash(plaintext)
        settings["hashed_password"] = hashed
        settings["plaintext_password"] = ""
    elif settings["hashed_password"] == "":
        logging.error("❌ No hashed password")
    else:
        logging.info("Found hashed password, probably")

    return in_settings


def check_ip(in_ip_or_network):
    """Check if string is valid IP or Network"""
    one_success = False
    try:
        ipaddress.IPv4Address(in_ip_or_network)
        one_success = True
    except ipaddress.NetmaskValueError:
        pass
    except ipaddress.AddressValueError:
        pass

    try:
        ipaddress.IPv4Network(in_ip_or_network)
        one_success = True
    except ipaddress.NetmaskValueError:
        pass
    except ipaddress.AddressValueError:
        pass

    try:
        ipaddress.IPv6Address(in_ip_or_network)
        one_success = True
    except ipaddress.AddressValueError:
        pass

    try:
        ipaddress.IPv6Network(in_ip_or_network)
        one_success = True
    except ipaddress.NetmaskValueError:
        pass
    except ipaddress.AddressValueError:
        pass

    return one_success


def check_allowlist(conf):
    """Validate the list"""
    errors_occurred = False

    lines = conf.splitlines()
    lines.append("deny all;")
    lines = list(set(lines))
    lines.sort()

    # logging.info("Lines: \n" + str(lines))

    for line in lines:
        words = line.split(" ")
        if words[0] not in ["allow", "deny"]:
            logging.error("❌ First word in line isn't allow or deny: %s", line)
            errors_occurred = True

        if words[0] == "allow":  # TODO, this needs fixing to include ipv6, networks
            ip_to_check = words[1].replace(";", "")
            if not check_ip(ip_to_check):
                logging.error("❌ Invalid IP address/network: %s", line)
                errors_occurred = True

        if line[-1] != ";":
            logging.error("❌ No ';' at end of line: %s", line)
            errors_occurred = True

        if len(words) != 2:
            logging.error("❌ Word count validation failed for line: %s", line)
            errors_occurred = True

    conf = "\n".join(lines)

    if errors_occurred:
        logging.error('❌ Line validation failed, reverting to "deny all;" ')
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
            logging.info("Reloading nginx")
            time.sleep(1)
            try:
                subprocess.run(reload_nginx_command, check=True)
            except subprocess.CalledProcessError:
                logging.error("❌ Couldnt restart nginx, either: ")
                logging.error("Nginx isnt installed")
                logging.error("or")
                logging.error(
                    "Sudoers rule not created for this user (%s)", user_account
                )
                logging.error("Create and edit a sudoers file")
                logging.error(" visudo /etc/sudoers.d/%s", user_account)
                logging.error("And insert the text:")
                logging.error(
                    " %s ALL=(root) NOPASSWD: /usr/sbin/systemctl reload nginx",
                    user_account,
                )

            reload_nginx_pending = False


def revert_list_daily():
    """Reset list at 4am"""
    while True:
        logging.info("Adding subnets/ips from config file")

        # Revert list
        with open(settings["path_to_allowlist"], "w", encoding="utf8") as conf_file:
            conf_file.write("deny all;")

        for subnet in settings["allowed_subnets"]:
            write_allowlist_file(subnet)

        # Get the current time
        current_time = datetime.datetime.now().time()

        # Set the target time (4 AM)
        target_time = datetime.time(4, 0)

        # Calculate the time difference
        time_difference = datetime.datetime.combine(
            datetime.date.today(), target_time
        ) - datetime.datetime.combine(datetime.date.today(), current_time)

        # If the target time is already passed for today, add 1 day
        if time_difference.total_seconds() < 0:
            time_difference += datetime.timedelta(days=1)

        seconds_until_next_run = time_difference.total_seconds()

        logging.info(
            "🛌 Reverting allowlist in ~%s minutes",
            str(int(seconds_until_next_run / 60)),
        )

        # Sleep until the target time
        time.sleep(seconds_until_next_run)

        logging.info("It's 4am, reverting IP list to default")


def setup_logger(args):
    """APP LOGGING"""
    invalid_log_level = False
    loglevel = logging.INFO
    if args.loglevel:
        args.loglevel = args.loglevel.upper()
        if args.loglevel in LOGLEVELS:
            loglevel = args.loglevel
        else:
            invalid_log_level = True

    logging.basicConfig(
        format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=loglevel
    )

    logging.getLogger("waitress").setLevel(logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logger = logging.getLogger()
    formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(name)s:%(message)s")

    try:
        if args.logfile:
            filehandler = logging.FileHandler(args.logfile)
            filehandler.setFormatter(formatter)
            logger.addHandler(filehandler)
    except IsADirectoryError as exc:
        err = "You are trying to log to a directory, try a file"
        raise IsADirectoryError(err) from exc

    except PermissionError as exc:
        err = "The user running this does not have access to the file: " + args.logfile
        raise IsADirectoryError(err) from exc

    logging.info(" ----------")
    logging.info("🙋 Logger started")
    if invalid_log_level:
        logging.warning(
            "❗ Invalid logging level: %s, defaulting to INFO", {args.loglevel}
        )


def main():
    """Start Flask webapp"""

    if not os.path.exists(
        settings["path_to_allowlist"]
    ):  # Create if file doesn't exist
        with open(settings["path_to_allowlist"], "w", encoding="utf8") as conf_file:
            conf_file.write("deny all;")

    # Start thread: restart handler
    thread = threading.Thread(target=reload_nginx, daemon=True)
    thread.start()

    thread = threading.Thread(target=revert_list_daily, daemon=True)
    thread.start()

    serve(app, host=args.WEBADDRESS, port=args.WEBPORT, threads=2)

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
        "--loglevel",
        type=str,
        dest="loglevel",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    parser.add_argument(
        "-lf",
        "--logfile",
        type=str,
        dest="logfile",
        help="Log file full path",
    )
    args = parser.parse_args()

    setup_logger(args)

    # Settings File
    errors_loading = False
    if not os.path.exists(args.settingspath):
        errors_loading = True
        with open(args.settingspath, "w", encoding="utf8") as json_file:
            settings = {
                "path_to_allowlist": "ipallowist.conf",
                "plaintext_password": "",
                "hashed_password": "",
                "allowed_subnets": ["127.0.0.1/32"],
            }
            json.dump(
                settings, json_file, indent=2
            )  # indent parameter is optional for pretty formatting
        logging.info("No config file found, creating default")
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
            logging.info("Please set password in: %s", args.settingspath)

    if not errors_loading:
        try:
            main()
        except KeyboardInterrupt:
            print("\nExiting due to KeyboardInterrupt! 👋")
            sys.exit(130)

    logging.info("Exiting 👋")
    sys.exit(1)
