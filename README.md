# Allowlist App

## Run

### Dev

```bash
flask --app allowlist run
```

### Prod

Simple

```bash
poetry install --only main
.venv/bin/waitress-serve --host 127.0.0.1 --call allowlist:create_app
```

Complex

```bash
poetry install --only main
.venv/bin/waitress-serve \
    --listen "127.0.0.1:8080" \
    --trusted-proxy '*' \
    --trusted-proxy-headers 'x-forwarded-for' \
    --log-untrusted-proxy-headers \
    --clear-untrusted-proxy-headers \
    --threads 4 \
    --call allowlist:create_app
```

## TODO

- `detect-test-pollution --failing-test tests/test_nginx.py::test_nginx_reload --tests tests`

### Later

- make the loading for the allowlist less cringe
- make settings better, nginx needs it's own path
- ipv6 support
- Tests
- publish whl
