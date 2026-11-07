#!/command/with-contenv bashio
# shellcheck shell=bash
set -Eeuo pipefail

if [[ -z "${CF_API_TOKEN:-}" ]]; then
    bashio::log.error "Cloudflare API token is required. Set it in the app configuration."
    exit 1
fi

mkdir -p /data/caddy /data/config
chmod 700 /data/caddy /data/config

# init-caddy-config validates and writes /data/Caddyfile before this service starts.
export XDG_DATA_HOME=/data
export XDG_CONFIG_HOME=/data/config
bashio::log.info "Starting Caddy with persistent certificate storage."
exec /usr/bin/caddy run --config /data/Caddyfile --adapter caddyfile
