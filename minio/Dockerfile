FROM minio/minio:latest

LABEL \
    io.hass.version="1.0.3" \
    io.hass.type="addon" \
    io.hass.arch="aarch64|amd64" \
    io.hass.name="MinIO" \
    io.hass.description="MinIO is an object storage server compatible with Amazon S3."

# Install jq (Alpine)
RUN apk add --no-cache jq

COPY run.sh /run.sh
RUN chmod +x /run.sh

ENTRYPOINT [ "/run.sh" ]
