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

### Optional per-route Basic Auth and upstream header

Set `basic_auth_username` and `basic_auth_password` together to require HTTP Basic Auth on that route's hostname. The password is passed to the Caddy hash command through stdin; the generated `basic_auth` directive explicitly selects Argon2id to match the stored hash. Route-level authentication covers the entire configured hostname, not a single path. If other paths on the same host must remain public, use a carefully reviewed path-scoped Caddyfile drop-in instead.

Set `custom_header_name` and `custom_header_value` together to attach one fixed header to upstream requests. This is useful when an upstream webhook adapter expects a token header. The value is restricted to URL-safe characters, stored in `/data/caddy-secrets.env` with mode `0600`, and exported only to the add-on runtime; it is not embedded in `/data/Caddyfile`. `Authorization` is reserved: the add-on strips inbound `Authorization` before proxying, so the upstream does not receive ADO's Basic Auth credentials.

For example, configure secrets through Supervisor's YAML editor and `secrets.yaml`:

```yaml
domain: mt-home.uk
cloudflare_api_token: !secret caddy_cloudflare_api_token
routes:
  - subdomain: ai
    target: 10.30.20.20:8765
    basic_auth_username: ado-webhook
    basic_auth_password: !secret caddy_ado_basic_auth
    custom_header_name: X-Gitlab-Token
    custom_header_value: !secret hermes_webhook_token
```

Keep the referenced values in Home Assistant's `secrets.yaml`, use separate strong values for the Basic Auth password and Hermes token, and rotate any value that may have been exposed. Supervisor resolves `!secret` before writing `/data/options.json`; do not paste secret values into shared documentation or treat a `!secret` tag as a literal password. See the [versioned ADO router example](examples/ado-workitem-router/README.md) and [Caddyfile drop-in](examples/ado-workitem-webhook.caddy).

## Home Assistant Reverse Proxy Trust (Important)

When routing traffic through Caddy to Home Assistant (`homeassistant:8123`), Home Assistant must trust the reverse proxy before it accepts the forwarded client address. Without the matching settings, Home Assistant blocks proxied requests and may return HTTP 400 or log that a request from a reverse proxy was received but the HTTP integration is not configured for reverse proxies.

### Home Assistant 2026.8 and newer

Home Assistant 2026.8 moved HTTP server configuration to the UI. Do not add or maintain the reverse-proxy settings in `configuration.yaml` for these releases; use:

1. Go to **Settings → System → Network**, then find the **HTTP server** section.
2. Turn on **Trust X-Forwarded-For**.
3. Add the **actual Caddy proxy IP address as seen by Home Assistant** to **Trusted proxies**. Determine this for your own installation, such as by checking the source address in Home Assistant's reverse-proxy error/log entry and confirming the Caddy add-on's assigned network address. The address to trust is the Caddy-to-Home-Assistant connection peer, not the public IP of a browser or client.
4. Save the HTTP server settings. Home Assistant restarts. When the UI returns, review the proposed change (the Italian UI labels this step **“Esamina la modifica”**) and explicitly confirm it within **5 minutes**. If it is not confirmed during that window, Home Assistant automatically rolls the settings back to the previous values.

Trust only the verified proxy address. Do not assume the default Supervisor/add-on network applies to every installation and do not add a broad subnet just to make the error disappear. Prefer a single proxy IP when stable. Use a CIDR only when needed and after verifying that it is the smallest network containing the proxy; when entering a CIDR, use its network address (for example, `192.168.1.0/24`), not a host address with a mask (for example, `192.168.1.50/24`).

If an existing `http:` YAML block was imported during upgrade, check the values in the UI and follow Home Assistant's migration/Repair guidance to remove the obsolete block from `configuration.yaml`.

### Home Assistant versions older than 2026.8

Before 2026.8, configure reverse-proxy trust in `configuration.yaml`. Replace the documentation-only address below with the actual Caddy proxy IP verified for your installation. Do not substitute a broad subnet unless it is required, verified, and narrowly scoped.

```yaml
http:
  use_x_forwarded_for: true
  trusted_proxies:
    - 192.0.2.10  # Example only: replace with the actual Caddy proxy IP
```

Restart Home Assistant after editing the YAML configuration.

See the [official Home Assistant HTTP integration documentation](https://www.home-assistant.io/integrations/http/) for the current UI fields, reverse-proxy requirements, CIDR format, five-minute confirmation/rollback, and YAML migration instructions.

## Extend with Caddyfile drop-ins

You can add custom Caddy configurations by creating `.caddy` files under `/share/caddy/conf.d/` in the Home Assistant share. The add-on automatically monitors this directory and reloads Caddy whenever a file is added, modified, or removed.

Example (`/share/caddy/conf.d/metrics.caddy`):

```caddyfile
@metrics host metrics.example.com
reverse_proxy @metrics prometheus:9090
```

> ⚠️ **Note**: Drop-ins are executable proxy directives. Only trusted administrators should have write access to `/share/caddy/conf.d/`. The add-on mounts `/share` as read-only. When a configuration change occurs, the add-on validates the new configuration before reloading; if syntax validation fails, Caddy keeps running with the previous valid configuration.

## ADO webhook example (optional)

The add-on itself stays provider-agnostic. The files under `examples/` are an optional, site-specific example for routing Azure DevOps Web Hooks to a Hermes webhook adapter; they are not defaults and are not built into the generic route generator.

1. Configure the `ai` route shown above with target `10.30.20.20:8765`, a distinct Basic Auth username/password, and a distinct `X-Gitlab-Token` custom header value.
2. Copy [`examples/ado-workitem-webhook.caddy`](examples/ado-workitem-webhook.caddy) to `/share/caddy/conf.d/ado-workitem-webhook.caddy`. It matches only host `ai.mt-home.uk` and exact paths `/webhook` and `/webhook/`, then rewrites them to `/webhooks/ado-workitems`; the generic route proxies to Hermes on port 8765.
3. Set the ADO Service Hooks target to `https://ai.mt-home.uk/webhook/` and configure the same Basic Auth credential. Keep the Hermes token in the configured `X-Gitlab-Token` header field on the Caddy route; do not put credentials in the URL.
4. Use HTTPS. The Basic Auth credential and Hermes token are separate secrets. `X-Gitlab-Token` is a static shared token, not an HMAC request signature or proof that the payload was generated by ADO; the receiver must validate events and re-read authoritative ADO state.
5. Install the versioned router skill from [`examples/ado-workitem-router/README.md`](examples/ado-workitem-router/README.md) only if you use the companion Hermes route. The add-on itself does not install or run a webhook receiver.

**Rollback order:** pause/disable the ADO subscriptions first so they stop sending to the endpoint; restore the previous add-on options/version and remove or restore the Caddy drop-in; restart and verify the prior proxy route; only then re-enable the subscriptions. Keep a backup of the current add-on data and configuration before changing versions.

## Security and Network Behavior

- The add-on only exposes host TCP ports 80 and 443 and mounts `/share` read-only; it does not require `host_network: true`, `privileged` mode, Docker socket access, or elevated Supervisor roles.
- The Cloudflare token is kept in a private S6 environment file with mode `0600`; it is not logged or written into the Caddyfile. The password-hashing subprocess receives a sanitized environment without `CF_API_TOKEN`.
- `/data/options.json`, `/data/caddy-secrets.env`, and `/data/Caddyfile` are backup-sensitive. They contain resolved add-on options, custom header secrets, and Basic Auth Argon2id hashes respectively. Protect backups; the generated Caddyfile does not contain plaintext Basic Auth passwords or custom-header values.
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
- **Home Assistant HTTP 400 / forwarded-header error**: The add-on sends an IP-only `X-Forwarded-For`. If using a custom drop-in, use `{http.request.remote.host}`, not `{remote}`, which includes the client port. Also review the Home Assistant reverse-proxy trust settings described above, using the actual Caddy proxy IP seen by Home Assistant.

## Build and Test

The add-on compiles Caddy with the Cloudflare DNS module (`github.com/caddy-dns/cloudflare`) in a pinned multi-stage Docker build. 

The repository's `ci/scripts/lint_addon.sh caddy` verifies Dockerfile formatting, metadata, and shell scripts. Python unit tests cover route validation, Caddyfile generation, and S6 service layout:

```bash
python -m unittest discover -s tests
```
