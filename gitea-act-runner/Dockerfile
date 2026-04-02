ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install jq to parse /data/options.json provided by the HA supervisor.
# Also create a stable symlink so act_runner is available at /usr/local/bin/act_runner
# regardless of where the base image places it (official image puts it at /act_runner).
RUN apk add --no-cache jq \
 && ln -sf "$(command -v act_runner 2>/dev/null || echo /act_runner)" /usr/local/bin/act_runner

COPY run.sh /run.sh
RUN chmod +x /run.sh

ENTRYPOINT ["/run.sh"]
