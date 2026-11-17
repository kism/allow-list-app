#!/usr/bin/env python3
"""One-off: convert a v0.2 (Flask) config.toml to the v0.3 config.json, validated with the app's Config.

Usage: .venv/bin/python scripts/migrate_config.py /etc/allowlistapp/config.toml [instance_dir]

instance_dir defaults to the toml's directory. An existing config.json is never overwritten.
"""

import json
import sys
import tomllib
from pathlib import Path
from typing import Any

from allowlistapp.config import CONFIG_FILE_NAME, Config


def clean(d: dict[str, Any]) -> dict[str, Any]:
    """Drop empty strings, v0.2 used "" for unset, v0.3 uses null (which pydantic would read "" as a path '.')."""
    return {k: clean(v) if isinstance(v, dict) else v for k, v in d.items() if v != ""}  # ruff: ignore[compare-to-empty-string] # Keep false/0/[]


def main() -> None:
    """Convert, write, then load it the way the app does so it's validated and gets mode 600."""
    if len(sys.argv) not in {2, 3}:
        sys.exit(__doc__)

    toml_path = Path(sys.argv[1])
    instance_path = Path(sys.argv[2]) if len(sys.argv) == 3 else toml_path.parent  # ruff: ignore[magic-value-comparison] # Optional second arg
    json_path = instance_path / CONFIG_FILE_NAME

    if json_path.exists():
        sys.exit(f"{json_path} already exists, not overwriting")

    config = clean(tomllib.loads(toml_path.read_text(encoding="utf8")))
    config.pop("flask", None)  # No Flask anymore

    instance_path.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(config))
    try:
        Config.load(instance_path)
    except ValueError as exc:  # pydantic's ValidationError is a ValueError
        json_path.unlink()
        sys.exit(f"Converted config doesn't validate, nothing written:\n{exc}")

    print(f"Wrote {json_path}, start the app with --instance-path {instance_path}")  # ruff: ignore[print] # CLI output


if __name__ == "__main__":
    main()
