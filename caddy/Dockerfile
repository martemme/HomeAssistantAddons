ARG CADDY_VERSION=2.11.7
ARG CLOUDFLARE_DNS_VERSION=v0.2.4

FROM caddy:${CADDY_VERSION}-builder-alpine AS caddy-builder
ARG CADDY_VERSION
ARG CLOUDFLARE_DNS_VERSION
RUN xcaddy build "v${CADDY_VERSION}" \
    --with "github.com/caddy-dns/cloudflare@${CLOUDFLARE_DNS_VERSION}" \
    --output /usr/bin/caddy

FROM ghcr.io/home-assistant/base-python:3.14-alpine3.24
ARG BUILD_ARCH
ARG BUILD_VERSION

COPY --from=caddy-builder /usr/bin/caddy /usr/bin/caddy
COPY generate_caddyfile.py /usr/local/bin/generate_caddyfile.py
COPY watch_conf.py /usr/local/bin/watch_conf.py
COPY run.sh /usr/local/bin/run-caddy
COPY rootfs /

RUN chmod a+x \
    /usr/local/bin/generate_caddyfile.py \
    /usr/local/bin/watch_conf.py \
    /usr/local/bin/run-caddy \
    /etc/s6-overlay/s6-rc.d/init-caddy-config/run \
    /etc/s6-overlay/s6-rc.d/caddy/run \
    /etc/s6-overlay/s6-rc.d/caddy/finish \
    /etc/s6-overlay/s6-rc.d/watch-config/run \
    /etc/s6-overlay/s6-rc.d/watch-config/finish

LABEL \
    io.hass.type="app" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.version="${BUILD_VERSION}" \
    org.opencontainers.image.source="https://github.com/martemme/HomeAssistantAddons"
