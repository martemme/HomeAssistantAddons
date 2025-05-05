FROM minio/minio:latest

LABEL \
    io.hass.version="1.0.1" \
    io.hass.type="addon" \
    io.hass.arch="aarch64|amd64" \
    io.hass.name="MinIO" \
    io.hass.description="MinIO is an object storage server compatible with Amazon S3."

COPY run.sh /run.sh
RUN chmod +x /run.sh

ENTRYPOINT [ "/run.sh" ]
