#!/usr/bin/env bashio

CONFIG="/data/options.json"

# Build /etc/exports from configured shares
bashio::log.info "Configuring NFS exports..."
> /etc/exports

count=$(jq '.shares | length' "${CONFIG}")

if [ "${count}" -eq 0 ]; then
    bashio::log.warning "No shares configured, nothing to export."
else
    for i in $(seq 0 $((count - 1))); do
        FOLDER=$(jq -r ".shares[${i}].folder" "${CONFIG}")
        NETWORK=$(jq -r ".shares[${i}].allowed_network" "${CONFIG}")
        READ_ONLY=$(jq -r ".shares[${i}].read_only" "${CONFIG}")
        MOUNT_PATH="/${FOLDER}"

        if [ "${READ_ONLY}" = "true" ]; then
            OPTIONS="ro,no_root_squash"
        else
            OPTIONS="rw,no_root_squash"
        fi

        bashio::log.info "Exporting ${MOUNT_PATH} to ${NETWORK} (${OPTIONS})..."
        echo "${MOUNT_PATH} ${NETWORK}(${OPTIONS})" >> /etc/exports
    done
fi

cat /etc/exports

# Start unfs3 user-space NFS server in foreground
bashio::log.info "Starting unfs3 NFS server..."
exec unfsd -d -e /etc/exports
