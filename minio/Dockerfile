FROM alpine:3.18

LABEL io.hass.name="MinIO"
LABEL io.hass.description="MinIO is a High Performance Object Storage, API compatible with Amazon S3 cloud storage service."
LABEL io.hass.arch="amd64|aarch64"
LABEL io.hass.type="addon"
LABEL io.hass.version="1.1.1"

# Install curl, jq and ca-certificates
RUN apk add --no-cache bash curl jq ca-certificates

# Install the latest version of MinIO
# https://min.io/download#/linux
# https://docs.min.io/docs/minio-server-quickstart-guide.html
RUN curl -fsSL https://dl.min.io/server/minio/release/linux-amd64/minio \
    -o /usr/local/bin/minio && \
    chmod +x /usr/local/bin/minio

# Copy the script into the container
# make it executable and run it
COPY run.sh /run.sh
RUN chmod +x /run.sh

ENTRYPOINT [ "/run.sh" ]
