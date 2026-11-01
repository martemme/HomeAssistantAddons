# Changelog

## 0.1.4

- Send an IP-only `X-Forwarded-For` value to upstreams, avoiding `IP:port` values that Home Assistant may reject with HTTP 400.

## 0.1.3

- Generalize documentation and default configuration for community homelab setups.
- Add official Caddy icon and logo assets for Home Assistant Supervisor Add-on Store display.
- Add comprehensive README with configuration parameters, trusted-proxy instructions, and security guidelines.

## 0.1.2

- Scope the token to Caddy's startup check while retaining its private S6 runtime environment file.

## 0.1.1

- Fix S6 user-bundle registration so the app starts correctly on Home Assistant.
- Build the Caddy binary for both amd64 and arm64 targets.

## 0.1.0

- Initial Caddy 2 app with Cloudflare DNS-01 wildcard TLS.
- Configurable subdomain-to-upstream routes and read-only Caddyfile drop-ins.
