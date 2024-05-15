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
    --listen "*:$PORT" \
    --trusted-proxy '*' \
    --trusted-proxy-headers 'x-forwarded-for x-forwarded-proto x-forwarded-port' \
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
* Template the allowlist
* ipv6 support
* Tests
