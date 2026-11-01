# Home Assistant Add-on: Caddy 2 Dynamic Ingress

![Supports amd64 Architecture][amd64-shield]
![Supports aarch64 Architecture][aarch64-shield]

This add-on provides a **Caddy 2 reverse proxy** with automatic wildcard TLS via Cloudflare DNS-01, perfect for:

- Secure remote access to Home Assistant and homelab services under your own domain
- Automatic wildcard and apex SSL/TLS certificates (`*.example.com` and `example.com`) via Let's Encrypt / ZeroSSL without exposing port 80 to the public internet
- Dynamic subdomain-to-upstream routing without modifying core Home Assistant configurations
- Custom Caddyfile drop-in support (`/share/caddy/conf.d/*.caddy`) with automatic hot-reload on changes

---

## 🚀 Features

- **Automated Wildcard TLS**: Obtains and renews wildcard certificates using the Cloudflare DNS-01 challenge.
- **Dynamic Routing**: Route clean subdomains (e.g., `home.example.com`, `vault.example.com`) directly to internal Docker containers, add-ons, or LAN hosts.
- **Zero Config Tampering**: Leaves Home Assistant core container configuration untouched; communicates via standard internal proxying.
- **Drop-in Extensibility**: Add custom reverse proxies, security headers, or authentication layers in `/share/caddy/conf.d/`.
- **Hot-Reload & Safety**: Inotify watcher automatically validates syntax before applying changes; faulty configs are rejected while keeping the existing service alive.
- **Production Hardened**: Token is kept in a restricted runtime environment (mode 0600) and stripped from process environment; container runs without root host privileges.

---

## ⚙️ Configuration

Example configuration in the Home Assistant add-on options:

```yaml
domain: example.com
cloudflare_api_token: your-cloudflare-api-token
email: admin@example.com
routes:
  - subdomain: home
    target: homeassistant:8123
  - subdomain: vault
    target: vaultwarden:80
  - subdomain: storage
    target: minio:9001
  - subdomain: media
    target: jellyfin:8096
```

### Parameters

| Variable | Default | Description |
|---|---|---|
| `domain` | `example.com` | Base apex domain managed in your Cloudflare DNS account. |
| `cloudflare_api_token` | *(Required)* | Cloudflare API Token with `Zone:Read` and `DNS:Edit` permissions. Supports `!secret` references. |
| `email` | `null` | *(Optional)* ACME email address for certificate expiration and renewal notifications. |
| `routes` | `[{"subdomain": "home", "target": "homeassistant:8123"}]` | List of routes mapping subdomains to upstream target services. |
| `routes[].subdomain` | `home` | DNS label under `domain` (e.g., `home` becomes `home.example.com`). Multi-level labels (e.g. `auth.app`) are supported. |
| `routes[].target` | `homeassistant:8123` | Upstream target address: `host:port`, `[IPv6]:port`, `http://host:port`, or `https://host:port`. |

---

## 🚀 Installation

1. In Home Assistant, navigate to **Settings → Add-ons → Add-on Store**.
2. Click the three dots **⋮** (top right) → **Repositories**, and add:
   ```
   https://github.com/martemme/HomeAssistantAddons
   ```
3. Locate **Caddy 2 Dynamic Ingress** and click **Install**.
4. In the **Configuration** tab, specify your `domain`, `cloudflare_api_token`, and desired `routes`.
5. *(Optional)* Add Home Assistant trusted proxy configuration (see below).
6. Start the add-on and inspect the logs.

---

## 🌐 Home Assistant Trusted Proxy Configuration

For **Home Assistant 2026.8 and newer**, configure reverse-proxy trust in the UI:

1. Open **Settings → System → Network** and find **HTTP server**.
2. Enable **Trust X-Forwarded-For**.
3. Under **Trusted proxies**, add the actual IP address of this Caddy add-on as Home Assistant sees it. Find and verify that address for your installation (for example, from Home Assistant's reverse-proxy error/log entry and your add-on network assignment); it is not the public address of the remote browser. Use a CIDR only if the proxy's address genuinely requires it, and verify the exact, smallest network. Do not copy a generic subnet or trust a broad network by default.
4. Save the settings. Home Assistant restarts; when it returns, review the proposed change and confirm it using **“Esamina la modifica”** (or the equivalent review prompt in your UI). Confirm within **5 minutes**. If you do not confirm in time, Home Assistant automatically restores the previous settings.

For Home Assistant versions **older than 2026.8**, configure the HTTP integration in `configuration.yaml` instead, replacing the example address with the verified Caddy proxy IP:

```yaml
http:
  use_x_forwarded_for: true
  trusted_proxies:
    - 192.0.2.10  # Example only: replace with the actual Caddy proxy IP
```

Do not use the legacy YAML block as the configuration method on 2026.8 or newer; follow Home Assistant's migration guidance if an existing `http:` block was imported. See the [official Home Assistant HTTP integration documentation](https://www.home-assistant.io/integrations/http/) for current options and migration details.

---

## 🧩 Caddyfile Drop-ins (`/share/caddy/conf.d/`)

You can extend Caddy with advanced directives (rate limiting, basic auth, extra headers, internal redirects) by adding `.caddy` files to `/share/caddy/conf.d/`.

Example (`/share/caddy/conf.d/metrics.caddy`):

```caddyfile
@metrics host metrics.example.com
reverse_proxy @metrics prometheus:9090
```

The add-on continuously monitors this folder. When a file is created, updated, or removed, Caddy runs a syntax validation. If valid, it seamlessly reloads without downtime.

---

## 🧾 Requirements

- Home Assistant OS or Supervised installation
- Supported architectures: `amd64`, `aarch64`
- Host TCP ports `80` and `443` free and assigned to the add-on
- Cloudflare-managed domain with an API token scoped to:
  - `Zone.Zone: Read`
  - `Zone.DNS: Edit`

---

## 📂 Repository Structure

```bash
caddy/
├── CHANGELOG.md             # Version history
├── config.json              # Add-on definition and options schema
├── DOCS.md                  # Comprehensive in-depth documentation
├── Dockerfile               # Multi-stage build with xcaddy & Cloudflare DNS
├── generate_caddyfile.py    # Safe Caddyfile compiler & validator
├── icon.png                 # Add-on store icon
├── logo.png                 # Add-on store banner logo
├── README.md                # Add-on overview
├── rootfs/                  # S6-overlay v3 init & runtime services
│   └── etc/s6-overlay/
│       ├── s6-rc.d/
│       └── user-bundles.d/
├── run.sh                   # S6 startup entrypoint
├── tests/                   # Automated unit & regression tests
├── translations/            # UI translation strings
└── watch_conf.py            # Inotify watcher for conf.d drop-ins
```

---

## 🛡 Security

- **Restricted Token Scope**: The Cloudflare API token is injected into an isolated, temporary S6 environment file (`0600`) and cleared from child environment variables. It is never printed in logs or written into the Caddyfile.
- **Strict Input Validation**: Subdomain labels and upstream targets are validated against strict regex rules before writing the Caddyfile, preventing syntax injection attacks.
- **Least Privilege**: The container operates without host networking (`host_network: false`), without privileged Docker mode, and mounts `/share` as read-only.

---

## 🪙 Comprami token

Ti è stato utile questo add-on o ti ha semplificato la gestione del tuo homelab?
Supporta lo sviluppo offrendomi dei token per continuare ad alimentare e testare modelli di intelligenza artificiale nei progetti open-source!

[![Comprami token](https://img.shields.io/badge/🪙%20Support-Comprami%20token-blueviolet?style=for-the-badge)](#)

---

## Changelog & Releases

Releases are based on [Semantic Versioning][semver], and use the format
of `MAJOR.MINOR.PATCH`. In a nutshell, the version will be incremented
based on the following:

- `MAJOR`: Incompatible or major changes.
- `MINOR`: Backwards-compatible new features and enhancements.
- `PATCH`: Backwards-compatible bugfixes and package updates.

See [CHANGELOG.md](CHANGELOG.md) for details on recent releases.

---

[semver]: http://semver.org/spec/v2.0.0.html
[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[repository-badge]: https://img.shields.io/badge/Add%20repository%20to%20my-Home%20Assistant-41BDF5?logo=home-assistant&style=for-the-badge
[repository-url]: https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fmartemme%2FHomeAssistantAddons
