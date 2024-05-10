#!/usr/bin/env python3
"""Flask webapp to control a nginx allowlist"""

import argparse
import os
import threading

from flask import Flask, render_template  # , request  # , Blueprint  # , jsonify

# from waitress import serve
# from werkzeug.middleware.proxy_fix import ProxyFix

from . import logger


def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # Register my libraries
    from . import allowlist
    from .settings import get_settings

    settings = get_settings()

    # Blueprints
    from . import auth

    app.register_blueprint(auth.bp)

    @app.route("/")
    def home():
        """Flask Home"""
        return render_template("home.html.j2")

    if not os.path.exists(settings["path_to_allowlist"]):  # Create if file doesn't exist
        with open(settings["path_to_allowlist"], "w", encoding="utf8") as conf_file:
            conf_file.write("deny all;")

    # Start thread: restart handler
    thread = threading.Thread(target=allowlist.reload_nginx, daemon=True)
    thread.start()

    thread = threading.Thread(target=allowlist.revert_list_daily, daemon=True)
    thread.start()

    # serve(app, host=args.WEBADDRESS, port=args.WEBPORT, threads=2)
    # app.run(host=args.WEBADDRESS, port=args.WEBPORT)
    # thread.join()

    return app


def get_args():
    return args


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

    logger.setup_logger(args)
