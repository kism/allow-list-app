# Allowlist App

## Run

### Dev

```bash
flask --app allowlist run
```

### Prod

Simple

```bash
waitress-serve --host 127.0.0.1 --call allowlist:create_app
```

Complex

```bash
waitress-serve \
    --listen "127.0.0.1:8080" \
    --trusted-proxy '*' \
    --trusted-proxy-headers 'x-forwarded-for' \
    --log-untrusted-proxy-headers \
    --clear-untrusted-proxy-headers \
    --threads 4 \
    --call allowlist:create_app
```

## TODO

* ~~Config items for always allowed networks and such~~
* ~~Revert every day~~
* ~~Real logging~~
* ~~Adopt the suggested Flask structure~~
* ~~use waitress, set threads~~
* ~~jf login~~
* better yaml
* ~~Template the allowlist~~
* Log to different loggers
* ~~js test to check if authed~~
* ~~redirect when success~~
* single page, only javascript

### Later

* ipv6 support
* Tests
* publish whl
