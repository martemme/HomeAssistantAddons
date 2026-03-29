FROM alpine:3.19
RUN apk add --no-cache nfs-utils
COPY run.sh /
RUN chmod +x /run.sh
CMD ["/run.sh"]