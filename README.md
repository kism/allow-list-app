# Allowlist App

![Check](https://github.com/kism/allow-list-app/actions/workflows/check.yml/badge.svg)
![Test](https://github.com/kism/allow-list-app/actions/workflows/test.yml/badge.svg)
[![codecov](https://codecov.io/gh/kism/allow-list-app/graph/badge.svg?token=2376WBPJE6)](https://codecov.io/gh/kism/allow-list-app)



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

### Todo

- ipv6 support
- opnsense
