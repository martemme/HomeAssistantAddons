FROM minio/minio:latest

LABEL \
  io.hass.version="1.0" \
  io.hass.type="addon" \
  io.hass.arch="aarch64|amd64"

COPY run.sh /usr/local/bin/run.sh
RUN chmod +x /usr/local/bin/run.sh

CMD ["/usr/local/bin/run.sh"]
