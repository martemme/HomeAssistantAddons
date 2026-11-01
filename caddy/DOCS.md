# Caddy 2 Dynamic Ingress

Caddy terminates public HTTPS for your base domain (e.g., `example.com` and `*.example.com`), then proxies each configured hostname to an internal HTTP or HTTPS upstream service. Home Assistant remains an upstream (typically at `homeassistant:8123`); this add-on does not alter Home Assistant configuration or install certificates directly into Home Assistant.

## Requirements

- A domain managed through Cloudflare DNS.
- A Cloudflare API token scoped to `Zone:Read` and `DNS:Edit` for your target domain (or all zones).
- Host TCP ports 80 and 443 available on the Home Assistant host when the add-on starts.
  - DNS-01 challenge is used for certificate issuance, so port 80 is not required for ACME validation, but it is used for automatic HTTP-to-HTTPS redirects.
- A Home Assistant version supporting Supervisor add-on configurations.

The first successful ACME request creates temporary `_acme-challenge` TXT records in Cloudflare via the DNS-01 API; Caddy automatically cleans them up after validation. Certificates and ACME account data are stored under `/data` inside the add-on container so they persist across restarts, updates, and Supervisor backups.

## Configuration

1. Install the add-on from the repository in the Home Assistant Add-on Store.
2. In the **Configuration** tab:
   - **`domain`**: Enter your base/apex domain (e.g. `example.com`).
   - **`cloudflare_api_token`**: Provide your Cloudflare API token. The field is masked in the UI; you can also use Home Assistant `!secret` references (e.g. `!secret cloudflare_token`).
   - **`email`** *(optional)*: Contact email address for ACME/Let's Encrypt renewal notifications.
   - **`routes`**: Define pairs of `subdomain` and `target`.
3. Save the configuration and start the add-on.

### Example Routes

```json
[
  {"subdomain": "home", "target": "homeassistant:8123"},
  {"subdomain": "vault", "target": "vaultwarden:80"},
  {"subdomain": "storage", "target": "minio:9001"},
  {"subdomain": "media", "target": "jellyfin:8096"}
]
```

- **`subdomain`**: Must be a valid DNS label beneath the configured base domain (e.g., `home` maps to `home.example.com`). Multi-level labels (e.g. `auth.app`) are supported.
- **`target`**: Can be `host:port`, `[IPv6-address]:port`, `http://host:port`, or `https://host:port`.
- Duplicate subdomains and malicious Caddyfile syntax injection are strictly validated and rejected on startup.

## Home Assistant Reverse Proxy Trust (Important)

When routing external traffic through Caddy to Home Assistant (`homeassistant:8123`), Home Assistant requires you to declare Caddy as a trusted reverse proxy in your `configuration.yaml`. If you see HTTP 400 errors or "A request from a reverse proxy was received from <IP>, but your HTTP integration is not set-up for reverse proxies", add the following to `configuration.yaml`:

```yaml
http:
  use_x_forwarded_for: true
  trusted_proxies:
    - 172.30.32.0/23  # Default Docker network subnet for Home Assistant Supervisor add-ons
    - 127.0.0.1
    - ::1
```

Restart Home Assistant after updating `configuration.yaml`.

## Extend with Caddyfile drop-ins

You can add custom Caddy configurations by creating `.caddy` files under `/share/caddy/conf.d/` in the Home Assistant share. The add-on automatically monitors this directory and reloads Caddy whenever a file is added, modified, or removed.

Example (`/share/caddy/conf.d/metrics.caddy`):

```caddyfile
@metrics host metrics.example.com
reverse_proxy @metrics prometheus:9090
```

> ⚠️ **Note**: Drop-ins are executable proxy directives. Only trusted administrators should have write access to `/share/caddy/conf.d/`. The add-on mounts `/share` as read-only. When a configuration change occurs, the add-on validates the new configuration before reloading; if syntax validation fails, Caddy keeps running with the previous valid configuration.

## Security and Network Behavior

- The add-on only exposes host TCP ports 80 and 443 and mounts `/share` read-only; it does not require `host_network: true`, `privileged` mode, Docker socket access, or elevated Supervisor roles.
- The Cloudflare token is kept securely in the add-on's private S6 environment runtime file (mode 0600) and is cleared from the generator environment. Secrets are never printed in logs or written into the static Caddyfile.
- Caddy passes standard proxy headers (`X-Forwarded-For`, `X-Forwarded-Proto`, `X-Forwarded-Host`); the add-on explicitly formats `X-Forwarded-For` as an IP only, without a port, for Home Assistant compatibility.
- Wildcard certificates (`*.example.com` and `example.com`) are generated via Let's Encrypt / ZeroSSL using Cloudflare DNS-01, meaning ports do not need to be open to the internet for issuance.

## Troubleshooting

- **Add-on fails to start / port bind error**: Another service (such as Nginx Proxy Manager or another reverse proxy) might already be listening on host port 80 or 443. Check that these ports are free.
- **ACME DNS challenge fails**:
  - Verify that your Cloudflare API token has `Zone:Read` and `DNS:Edit` permissions for the domain.
  - Verify public DNS propagation for the domain.
  - Check system clock / NTP synchronization on the host.
  - Check the add-on logs for specific ACME error messages.
- **502 Bad Gateway**: Verify that the target service hostname/IP and port are reachable from the add-on container network and that the service is running.
- **Drop-in configuration not reloading**: Ensure the file is placed in `/share/caddy/conf.d/`, ends with `.caddy`, and contains valid Caddyfile syntax. Check add-on logs for validation errors.
- **Home Assistant HTTP 400 / forwarded-header error**: The add-on sends an IP-only `X-Forwarded-For`. If using a custom drop-in, use `{http.request.remote.host}`, not `{remote}`, which includes the client port. Also review your Home Assistant `http` configuration as described in the [Home Assistant Reverse Proxy Trust](#home-assistant-reverse-proxy-trust-important) section.

## Build and Test

The add-on compiles Caddy with the Cloudflare DNS module (`github.com/caddy-dns/cloudflare`) in a pinned multi-stage Docker build. 

The repository's `ci/scripts/lint_addon.sh caddy` verifies Dockerfile formatting, metadata, and shell scripts. Python unit tests cover route validation, Caddyfile generation, and S6 service layout:

```bash
python -m unittest discover -s tests
```
