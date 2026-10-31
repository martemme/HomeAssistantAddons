# syntax=docker/dockerfile:1.6
ARG CADDY_VERSION=2.11.7
ARG CLOUDFLARE_DNS_VERSION=v0.2.4

FROM --platform=$BUILDPLATFORM caddy:${CADDY_VERSION}-builder-alpine AS caddy-builder
ARG CADDY_VERSION
ARG CLOUDFLARE_DNS_VERSION
ARG TARGETOS
ARG TARGETARCH
RUN GOOS="${TARGETOS}" GOARCH="${TARGETARCH}" CGO_ENABLED=0 xcaddy build "v${CADDY_VERSION}" \
    --with "github.com/caddy-dns/cloudflare@${CLOUDFLARE_DNS_VERSION}" \
    --output /usr/bin/caddy

FROM ghcr.io/home-assistant/base-python:3.14-alpine3.24
ARG BUILD_ARCH
ARG BUILD_VERSION

COPY --from=caddy-builder --chmod=0755 /usr/bin/caddy /usr/bin/caddy
COPY --chmod=0755 generate_caddyfile.py /usr/local/bin/generate_caddyfile.py
COPY --chmod=0755 watch_conf.py /usr/local/bin/watch_conf.py
COPY --chmod=0755 run.sh /usr/local/bin/run-caddy
COPY rootfs /
COPY --chmod=0755 rootfs/etc/s6-overlay/s6-rc.d/init-caddy-config/run /etc/s6-overlay/s6-rc.d/init-caddy-config/run
COPY --chmod=0755 rootfs/etc/s6-overlay/s6-rc.d/caddy/run /etc/s6-overlay/s6-rc.d/caddy/run
COPY --chmod=0755 rootfs/etc/s6-overlay/s6-rc.d/caddy/finish /etc/s6-overlay/s6-rc.d/caddy/finish
COPY --chmod=0755 rootfs/etc/s6-overlay/s6-rc.d/watch-config/run /etc/s6-overlay/s6-rc.d/watch-config/run
COPY --chmod=0755 rootfs/etc/s6-overlay/s6-rc.d/watch-config/finish /etc/s6-overlay/s6-rc.d/watch-config/finish

LABEL \
    io.hass.type="app" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.version="${BUILD_VERSION}" \
    org.opencontainers.image.source="https://github.com/martemme/HomeAssistantAddons"
