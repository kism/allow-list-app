import sys
import yaml
import pwd
import os
from os.path import expanduser

from argon2 import PasswordHasher

ph = PasswordHasher()


class AllowListAppSettings:
    def __init__(self):
        # Set default values
        self.allowed_subnets = []
        self.allowlist_path = "ipallowlist.conf"
        self.password_hashed = ""
        self.password_cleartext = ""
        self.log_path = "allowlistapp.log"
        self.log_level = "INFO"
        self.settings_path = None

        paths = []
        paths.append(os.getcwd() + os.sep + "settings.yml")
        paths.append(expanduser("~/.config/allowlistapp/settings.yml"))
        paths.append("/etc/allowlistapp/settings.yml")

        for path in paths:
            if os.path.exists(path):
                print(f"Found settings at path: {path}", end="")
                if not self.settings_path:
                    print(", Using this path as it's the first one that was found")
                    self.settings_path = path
                else:
                    print()
            else:
                print("No settings file found at: " + path)

        if not self.settings_path:
            self.settings_path = paths[0]
            print("No configuration file found, creating at default location: " + self.settings_path)
            write_settings(self)
            self.settings_path = paths[0]  # TODO FIXME WTF WHY IS THIS REQUIRED

        # Load from path
        with open(self.settings_path, "r", encoding="utf8") as yaml_file:
            settings_temp = yaml.safe_load(yaml_file)

        # Get Real Values
        try:
            self.allowlist_path = settings_temp["allowlist_path"]
            self.allowed_subnets = settings_temp["allowed_subnets"]
            self.log_level = settings_temp["log_level"]
            self.log_path = settings_temp["log_path"]
            self.password_cleartext = settings_temp["password_cleartext"]
            self.password_hashed = settings_temp["password_hashed"]
        except (KeyError, TypeError):
            err_text = f"Error loading settings from: {self.settings_path}, remove: {self.settings_path} and run the app again to generate a new one"
            raise KeyError(err_text)  # TODO, find a better error or make your own

        self.password_cleartext, self.password_hashed = check_password(self)
        write_settings(self)


def check_password(ala_settings):
    # Settings File
    if ala_settings.password_cleartext == "" and ala_settings.password_hashed == "":
        print("Please set password in: " + ala_settings.settings_path)
        sys.exit(1)  # TODO, find a better error or make your own

    # Hash password if there is a plaintext password set
    if ala_settings.password_cleartext != "":
        print("Plaintext password set, hashing and removing from config file")
        plaintext = ala_settings.password_cleartext
        hashed = ph.hash(plaintext)
        ala_settings.password_hashed = hashed
        ala_settings.password_cleartext = ""
    elif ala_settings.password_hashed == "":
        print("❌ No hashed password")  # TODO This will never reach yeah?
    else:
        print("Found hashed password, probably")

    return ala_settings.password_cleartext, ala_settings.password_hashed


def write_settings(ala_settings):
    try:
        with open(ala_settings.settings_path, "w", encoding="utf8") as yaml_file:
            settings_write_temp = vars(ala_settings)
            del settings_write_temp["settings_path"]
            yaml.safe_dump(settings_write_temp, yaml_file)
    except PermissionError:
        user_account = pwd.getpwuid(os.getuid())[0]
        raise PermissionError(f"Fix permissions: chown {user_account} {ala_settings.settings_path}")
