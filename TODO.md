# TODO

The audit findings are fixed, these were left on purpose:

- **No cap on the allowlist size, no debounce on nginx reloads.** Every new IP needs a valid login, failed logins are
  rate limited, and `revert_daily` clears the list, so growth is bounded in practice. Add a cap if `revert_daily` is
  off and the user base is large.
- **The login limiter is in memory.** It resets on restart and is per process, same as the allowlist.
- ipv6 support in the README examples, opnsense.
