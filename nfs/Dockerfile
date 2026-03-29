ARG BUILD_FROM
FROM $BUILD_FROM
RUN apk add --no-cache nfs-utils bash
COPY run.sh /
RUN chmod +x /run.sh
CMD ["/run.sh"]