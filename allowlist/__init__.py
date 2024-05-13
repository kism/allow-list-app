#!/usr/bin/env python3
"""Flask webapp to control a nginx allowlist"""

import os
import threading
import tomllib

from flask import Flask, render_template  # , request  # , Blueprint  # , jsonify

ala_settings = None


def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    from . import settings

    global ala_settings
    ala_settings = settings.AllowListAppSettings()

    app = Flask(__name__, instance_relative_config=True)
    try:
        app.config.from_file("flask.toml", load=tomllib.load, text=False)
    except FileNotFoundError:
        print(f"No flask configuration file found at: {app.instance_path}{os.sep}flask.toml. Using defaults (this is not a problem).")

    # Register my libraries
    from . import allowlist
    from . import logger

    logger.setup_logger(ala_settings.log_level, ala_settings.log_path)

    # Blueprints
    from . import auth

    app.register_blueprint(auth.bp)

    @app.route("/")
    def home():
        """Flask Home"""
        return render_template("home.html.j2")

    if not os.path.exists(ala_settings.allowlist_path):  # Create if file doesn't exist
        with open(ala_settings.allowlist_path, "w", encoding="utf8") as conf_file:
            conf_file.write("deny all;")

    # Start thread: restart handler
    thread = threading.Thread(target=allowlist.reload_nginx, daemon=True)
    thread.start()

    thread = threading.Thread(target=allowlist.revert_list_daily, args=(ala_settings,), daemon=True)
    thread.start()

    # serve(app, host=args.WEBADDRESS, port=args.WEBPORT, threads=2)
    # app.run(host=args.WEBADDRESS, port=args.WEBPORT)
    # thread.join()

    return app


def get_ala_settings():
    return ala_settings
