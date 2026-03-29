FROM ghcr.io/hassio-addons/base:latest
RUN apk add --no-cache nfs-utils
COPY run.sh /
RUN chmod +x /run.sh
CMD ["/run.sh"]