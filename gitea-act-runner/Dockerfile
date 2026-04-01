ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install jq to parse /data/options.json provided by the HA supervisor
RUN apk add --no-cache jq

COPY run.sh /run.sh
RUN chmod +x /run.sh

ENTRYPOINT ["/run.sh"]
