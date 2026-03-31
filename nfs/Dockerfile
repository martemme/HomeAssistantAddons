ARG BUILD_FROM
FROM $BUILD_FROM
RUN apk add --no-cache unfs3 bash jq
COPY run.sh /
RUN chmod +x /run.sh
CMD ["/run.sh"]