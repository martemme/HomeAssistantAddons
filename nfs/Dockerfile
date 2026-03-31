ARG BUILD_FROM
FROM $BUILD_FROM
RUN echo "nameserver 8.8.8.8" > /etc/resolv.conf && apk add --no-cache nfs-utils bash
COPY run.sh /
RUN chmod +x /run.sh
CMD ["/run.sh"]