FROM debian:stable-slim

LABEL io.hass.name="MinIO"
LABEL io.hass.description="S3-compatible object storage for HA"
LABEL io.hass.arch="amd64|aarch64"
LABEL io.hass.type="addon"
LABEL io.hass.version="1.0.63"

# Install curl and jq then download MinIO binary
# https://min.io/download#/linux
# https://docs.min.io/docs/minio-server-quickstart-guide.html
RUN apt update && \
    apt install -y --no-install-recommends curl jq && \
    rm -rf /var/lib/apt/lists/* && \
    curl -fsSL https://dl.min.io/server/minio/release/linux-amd64/minio \
      -o /usr/local/bin/minio && \
    chmod +x /usr/local/bin/minio

# Copy the script into the container
# make it executable and run it
COPY run.sh /run.sh
RUN chmod +x /run.sh

ENTRYPOINT [ "/run.sh" ]
