#!/usr/bin/env python3
"""Flask webapp to control a nginx allowlist"""

import os
import threading
import tomllib

from flask import Flask, render_template  # , request  # , Blueprint  # , jsonify

app_settings = None


def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    global app_settings
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_file("config.toml", load=tomllib.load, text=False)

    with open("instance/config.toml", "rb") as f:
        app_settings = tomllib.load(f)

    from . import settings

    app_settings = settings.check(app_settings)

    for k, v in app.config.items():
        print(f"{k}: {v}")

    for k, v in app_settings.items():
        print(f"{k}: {v}")

    # Register my libraries
    from . import allowlist
    from . import logger

    logger.setup_logger(app_settings["loglevel"], app_settings["logpath"])

    # Blueprints
    from . import auth

    app.register_blueprint(auth.bp)

    @app.route("/")
    def home():
        """Flask Home"""
        return render_template("home.html.j2")

    if not os.path.exists(app_settings["path_to_allowlist"]):  # Create if file doesn't exist
        with open(app_settings["path_to_allowlist"], "w", encoding="utf8") as conf_file:
            conf_file.write("deny all;")

    # Start thread: restart handler
    thread = threading.Thread(target=allowlist.reload_nginx, daemon=True)
    thread.start()

    thread = threading.Thread(target=allowlist.revert_list_daily, args=(app_settings,), daemon=True)
    thread.start()

    # serve(app, host=args.WEBADDRESS, port=args.WEBPORT, threads=2)
    # app.run(host=args.WEBADDRESS, port=args.WEBPORT)
    # thread.join()

    return app


def get_app_settings():
    return app_settings
