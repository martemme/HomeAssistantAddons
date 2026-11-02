ARG BUILD_FROM=ghcr.io/home-assistant/base-debian:trixie
FROM timberio/vector:0.44.0-debian@sha256:f8933ff1a3ec08df45abc6130947938d98dc85792a25592ec1aa6fe83a7f562c AS vector
FROM ${BUILD_FROM}
ARG BUILD_ARCH
ARG BUILD_VERSION

# Vector's journald source invokes journalctl; the Alpine HA base does not provide it.
# Keep the package on the base image's current Debian security stream.
# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install --yes --no-install-recommends systemd \
    && rm -rf /var/lib/apt/lists/*

COPY --from=vector /usr/bin/vector /usr/local/bin/vector
COPY vector.yaml /etc/vector/vector.yaml
COPY run.sh /run.sh
COPY rootfs /

RUN chmod 0755 /run.sh /etc/s6-overlay/s6-rc.d/vector/run

LABEL \
    io.hass.type="app" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.version="${BUILD_VERSION}" \
    org.opencontainers.image.source="https://github.com/martemme/HomeAssistantAddons"
