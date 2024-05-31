"""Handles the Databse of the app."""

import csv
import ipaddress
import logging
import os
from datetime import datetime

CSV_SCHEMA = {"username": "", "ip": "", "date": ""}
logger = logging.getLogger("allowlist")


def get_allowlist() -> list:
    """Get the allowlist as a dict."""
    allowlist = []

    logger.debug("Building allowlist list from file...")
    try:
        with open(database_path, newline="") as csvfile:
            csv_reader = csv.DictReader(csvfile, quoting=csv.QUOTE_MINIMAL)
            allowlist = list(csv_reader)
    except FileNotFoundError:
        pass
    return allowlist


def insert_ip(username: str, ip: str) -> bool:
    """Insert an IP into the allowlist, returns if an IP has been inserted."""
    logger.debug("Trying to insert ip: %s for user: %s", ip, username)
    allowlist = get_allowlist()

    __check_ip(ip)

    logger.debug("Checking if IP allready in allowlist...")
    auth_in_list = False
    for item in allowlist:
        if item["ip"] == ip:
            logger.info("Duplicate auth! Not adding.")
            auth_in_list = True
            break

    if not auth_in_list:
        new_item = {"username": username, "ip": ip, "date": str(datetime.now())}

        allowlist.append(new_item)

        with open(database_path, "w", newline="") as csvfile:
            csv_writer = csv.DictWriter(
                csvfile,
                CSV_SCHEMA.keys(),
                delimiter=",",
                quotechar='"',
                quoting=csv.QUOTE_MINIMAL,
            )
            csv_writer.writeheader()
            for item in allowlist:
                csv_writer.writerow(item)
        logger.info("Added ip: %s to allowlist", ip)

    return not auth_in_list


def check_database() -> True:
    """Check the 'schema' of the database."""
    logger.info("Checking Database")
    try:
        with open(database_path, newline="") as csvfile:
            csv_reader = csv.reader(csvfile, quoting=csv.QUOTE_MINIMAL)
            for i, row in enumerate(csv_reader):
                if len(row) != len(CSV_SCHEMA.keys()):
                    err = f"Row {i + 1} of csv not three columns, fix or delete {database_path}"
                    raise ValueError(err)
        logger.info("Database checks passed")
    except FileNotFoundError:
        logger.info("Database file not found, that's okay")


def reset_database() -> None:
    """Clear the database."""
    logging.info("CLEARING THE DATABASE...")
    with open(database_path, "w", newline="") as csvfile:
        csv_writer = csv.DictWriter(csvfile, CSV_SCHEMA.keys(), delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writeheader()


def init_database(ala_settings: dict) -> None:
    """Takes in a list of IPs, adds to defualt user."""
    logging.info("Initialising the database...")
    for subnet in ala_settings.allowed_subnets:
        insert_ip("default", subnet)
    logging.info("Done initialising the database")


def __check_ip(in_ip_or_network: str) -> True:
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

    if not one_success:
        err = f"Invalid IP/network address: {in_ip_or_network}"
        raise ValueError(err)


database_path = os.getcwd() + os.sep + "database.csv"
