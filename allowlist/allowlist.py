#!/usr/bin/env python3
"""Flask webapp to control a nginx allowlist."""

import datetime
import ipaddress
import logging
import os
import pwd
import subprocess
import time

# TODO: from waitress import serve
# TODO: from werkzeug.middleware.proxy_fix import ProxyFix

reload_nginx_pending = False
write_file_in_progress = False


def write_allowlist_file(ala_settings: dict, ip: str) -> None:
    """Write to the nginx allowlist conf file."""
    global reload_nginx_pending
    global write_file_in_progress
    write_file_in_progress = True

    with open(ala_settings.allowlist_path, encoding="utf8") as conf_file:
        content = conf_file.read()

    with open(ala_settings.allowlist_path, "w", encoding="utf8") as conf_file:
        content = "allow " + ip + ";\n" + content
        content = check_allowlist(content)
        logging.debug("Content to write: \n", extra=content)
        conf_file.write(content)
        logging.info("Wrote config, allowing: %s", ip)

    write_file_in_progress = False
    reload_nginx_pending = True


def check_ip(in_ip_or_network: str) -> bool:
    """Check if string is valid IP or Network."""
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


def check_allowlist(conf: str) -> str:
    """Validate the list."""
    errors_occurred = False

    lines = conf.splitlines()
    lines.append("deny all;")
    lines = list(set(lines))
    lines.sort()
    words_per_line = 2

    for line in lines:
        words = line.split(" ")
        if words[0] not in ["allow", "deny"]:
            logging.error("❌ First word in line isn't allow or deny: %s", line)
            errors_occurred = True

        if words[0] == "allow":  # TODO: this needs fixing to include ipv6, networks
            ip_to_check = words[1].replace(";", "")
            if not check_ip(ip_to_check):
                logging.error("❌ Invalid IP address/network: %s", line)
                errors_occurred = True

        if line[-1] != ";":
            logging.error("❌ No ';' at end of line: %s", line)
            errors_occurred = True

        if len(words) != words_per_line:
            logging.error("❌ Word count validation failed for line: %s", line)
            errors_occurred = True

    conf = "\n".join(lines)

    if errors_occurred:
        logging.error('❌ Line validation failed, reverting to "deny all;" ')
        conf = "deny all;"

    return conf


def reload_nginx() -> None:
    """Reload nginx."""
    global reload_nginx_pending
    user_account = pwd.getpwuid(os.getuid())[0]

    reload_nginx_command = ["systemctl", "reload", "nginx"]
    if user_account != "root":
        reload_nginx_command = ["sudo", "systemctl", "reload", "nginx"]

    while True:
        time.sleep(1)
        if reload_nginx_pending:
            logging.info("Reloading nginx")
            while write_file_in_progress:  # TODO: this is unsafe
                time.sleep(1)

            try:
                result = None
                result = subprocess.run(reload_nginx_command, check=True, capture_output=True, text=True)  # noqa: S603 Input has been validated
            except subprocess.CalledProcessError:
                logging.exception("❌ Couldnt restart nginx, either: ")
                logging.exception("Nginx isnt installed")
                logging.exception("or")
                logging.exception("Sudoers rule not created for this user (%s)", user_account)
                logging.exception("Create and edit a sudoers file")
                logging.exception(" visudo /etc/sudoers.d/%s", user_account)
                logging.exception("And insert the text:")
                logging.exception(
                    " %s ALL=(root) NOPASSWD: /usr/sbin/systemctl reload nginx",
                    user_account,
                )

                logging.exception("")
                if result:
                    logging.exception("Full error just in case:")
                    logging.exception(result.stderr)
                else:
                    logging.exception("No stderr, not looking good, here is what Python says:")

            reload_nginx_pending = False


def revert_list_daily(ala_settings: dict) -> None:
    """Reset list at 4am."""
    while True:
        logging.info("Adding subnets/ips from config file")

        # Revert list
        with open(ala_settings.allowlist_path, "w", encoding="utf8") as conf_file:
            conf_file.write("deny all;")

        for subnet in ala_settings.allowed_subnets:
            write_allowlist_file(ala_settings, subnet)

        # Get the current time
        current_time = datetime.datetime.now().time()

        # Set the target time (4 AM)
        target_time = datetime.time(4, 0)

        # Calculate the time difference
        time_difference = datetime.datetime.combine(datetime.date.today(), target_time) - datetime.datetime.combine(
            datetime.date.today(),
            current_time,
        )

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
