# Allowlist App

[![Lint](https://github.com/kism/allow-list-app/actions/workflows/check.yml/badge.svg)](https://github.com/kism/allow-list-app/actions/workflows/check.yml)
[![Type Check](https://github.com/kism/allow-list-app/actions/workflows/check_types.yml/badge.svg)](https://github.com/kism/allow-list-app/actions/workflows/check_types.yml)
[![Test](https://github.com/kism/allow-list-app/actions/workflows/test.yml/badge.svg)](https://github.com/kism/allow-list-app/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/kism/allow-list-app/graph/badge.svg?token=2376WBPJE6)](https://codecov.io/gh/kism/allow-list-app)

Log in with a password (static, or via Jellyfin) and your IP gets added to an nginx `allow` list.

## Run

### Setup

```bash
uv sync --all-groups # Omit --all-groups for prod
```

### Dev

```bash
.venv/bin/python -m allowlistapp
```

Or with reload, note that this bypasses the argparse entrypoint:

```bash
.venv/bin/uvicorn --factory allowlistapp:create_app --reload --port 5000
```

### Prod

```bash
uv sync
.venv/bin/allowlistapp --host 127.0.0.1 --port 5000 --instance-path /etc/allowlistapp
```

Run a single process, the allowlist lives in memory. Put it behind nginx for TLS.

The client IP comes from `X-Forwarded-For` only when the request is from a proxy in `--forwarded-allow-ips`
(default `127.0.0.1`), and the rightmost untrusted address is used, so clients can't spoof it. In nginx:

```nginx
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
```

Five failed logins in a minute from one IP (or IPv6 /64) gets a 429 until the minute is up.

Access is per IP: everyone behind the same NAT or CGNAT address as someone who logged in gets in too.
With `revert_daily` the list goes back to `allowed_subnets` at 4am.

If not running as root, nginx is reloaded with `sudo systemctl reload nginx`, so add a sudoers rule:

```text
youruser ALL=(root) NOPASSWD: /usr/sbin/systemctl reload nginx
```

## Config

Upgrading from v0.2 (Flask, `config.toml`)? Convert it once, the hashed password carries over:

```bash
.venv/bin/python scripts/migrate_config.py /etc/allowlistapp/config.toml
```

`config.json` lives in the instance directory (`./instance` by default, override with `--instance-path`).
It is created with defaults on first run, and rewritten on every load with any missing fields filled in.
Set `auth.static.password_cleartext`, on the next start it is hashed and removed from the file.
Defaults, definitions and validation are all in `src/allowlistapp/config.py`.

```json
{
  "app": {
    "allowed_subnets": [],
    "auth_type": "static",
    "revert_daily": true,
    "redirect_url": "",
    "db_path": null
  },
  "services": {
    "nginx": {
      "enabled": false,
      "allowlist_path": null
    }
  },
  "auth": {
    "remote": {
      "url": null
    },
    "static": {
      "password_cleartext": "",
      "password_hashed": ""
    }
  },
  "logging": {
    "level": "INFO",
    "path": null
  }
}
```

`auth_type` is `static` or `jellyfin`, for jellyfin set `auth.remote.url`.
`allowed_subnets` are IPs or networks, host bits are dropped (`192.168.1.5/24` becomes `192.168.1.0/24`).

## Development

```bash
scripts/run-ci-local.sh  # ty, ruff, pytest
scripts/run-coverage.sh
```

### Todo

See [TODO.md](TODO.md)
