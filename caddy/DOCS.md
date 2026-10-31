# Caddy 2 Dynamic Ingress

Caddy terminates public HTTPS for `mt-home.uk` and `*.mt-home.uk`, then proxies each configured hostname to an HTTP or HTTPS upstream. Home Assistant remains an upstream at `homeassistant:8123`; this app does not rewrite Home Assistant configuration or install certificates into Home Assistant.

## Requirements

- A working Cloudflare API token scoped to `Zone:Read` and `DNS:Edit` for `mt-home.uk`.
- Host TCP ports 80 and 443 available when the app is started. This app uses DNS-01 for certificate issuance, so port 80 is not needed for ACME validation, but it is used for HTTP-to-HTTPS redirects.
- A Home Assistant version that supports the Supervisor app configuration in `config.json`.

The first successful ACME request creates temporary `_acme-challenge` TXT records in Cloudflare; Caddy removes them after validation. Caddy stores certificates and account data under `/data` so they survive restarts and are included in app backups.

## Configure

1. Install the app from the repository.
2. In Configuration, set the Cloudflare token. The field is hidden in the UI; do not paste it into Caddyfile drop-ins or logs. Home Assistant `!secret` references may be used for this option.
3. Keep `domain` as `mt-home.uk`, or set another domain managed by the same Cloudflare token.
4. Add routes as pairs of `subdomain` and `target`. The default route is `home` → `homeassistant:8123`.
5. Save and start/restart the app.

Example routes:

```json
[
  {"subdomain":"home","target":"homeassistant:8123"},
  {"subdomain":"dns","target":"a0d7b954-adguard:80"},
  {"subdomain":"storage","target":"minio:9001"},
  {"subdomain":"ai","target":"ai-service:8644"}
]
```

A target can be `host:port`, `[IPv6-address]:port`, `http://host:port`, or `https://host:port`. Each subdomain must be a DNS name beneath the configured base domain; duplicate names and Caddyfile syntax in route values are rejected.

## Extend with Caddyfile drop-ins

Create `/share/caddy/conf.d/` in the Home Assistant share and add one `.caddy` file per extension. The app imports matching files and reloads Caddy when their contents change. Example:

```caddyfile
@metrics host metrics.mt-home.uk
reverse_proxy @metrics prometheus:9090
```

Drop-ins are executable proxy configuration. Only trusted administrators and deployment automation should be able to write them. The app mounts `/share` read-only and never executes shell commands from those files. Validate a change in the app logs before relying on it; if a reload is rejected, the last valid Caddy configuration remains active.

## Security and network behavior

- The app requests only TCP 80/443 and a read-only `/share` mount; it does not use host networking, privileged mode, Docker API, or broad Supervisor API roles.
- The Cloudflare token is held in the app options and a runtime-only S6 environment file. It is not written into the generated Caddyfile; startup validation and reload output are suppressed so parser errors cannot echo secrets from the configuration.
- Caddy sends standard reverse-proxy forwarding headers. This app does not alter Home Assistant settings. If the existing Home Assistant proxy trust policy rejects requests from the Supervisor app network, resolve that prerequisite before cutover; do not disable Home Assistant protection globally.
- The Supervisor `ingress` feature is unrelated: this app is an external reverse proxy, not an embedded Home Assistant app panel.

## Troubleshooting

- **App cannot start / bind error:** another app may already own host port 80 or 443. Stop or reconfigure that service only after preserving its existing proxy routes.
- **ACME DNS challenge fails:** verify Cloudflare token scope, public resolution of the zone, system time, and the Caddy log. Existing unrelated `_acme-challenge` records are not automatically deleted by this app.
- **Route returns 502:** verify the target hostname/port is reachable from the Supervisor app network and that the upstream speaks the expected protocol.
- **A drop-in does not apply:** check that it is under `/share/caddy/conf.d/`, has a `.caddy` suffix, and is valid Caddyfile syntax. A failed reload keeps the last working config.
- **Home Assistant reports an untrusted proxy:** review the existing trusted-proxy settings before cutover; this app never edits them.

## Build and test

The app builds Caddy with the Cloudflare DNS module in a pinned multi-stage Docker build. The repository's `ci/scripts/lint_addon.sh caddy` checks Dockerfile, metadata, and shell scripts; Python unit tests cover route validation and Caddyfile generation. A local Docker build checks the target architecture. A real HAOS installation is required to verify Supervisor behavior and ACME issuance.
