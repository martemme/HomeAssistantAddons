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
        bashio::log.info "Setting permissions on /${FOLDER}..."
        chmod 777 "/${FOLDER}"
        NETWORK=$(jq -r ".shares[${i}].allowed_network" "${CONFIG}")
        READ_ONLY=$(jq -r ".shares[${i}].read_only" "${CONFIG}")
        ROOT_SQUASH=$(jq -r ".shares[${i}].root_squash" "${CONFIG}")
        MOUNT_PATH="/${FOLDER}"

        if [ "${READ_ONLY}" = "true" ]; then
            OPTIONS="ro"
        else
            OPTIONS="rw"
        fi

        if [ "${ROOT_SQUASH}" = "true" ]; then
            OPTIONS="${OPTIONS},root_squash"
        else
            OPTIONS="${OPTIONS},no_root_squash"
        fi
        OPTIONS="${OPTIONS},insecure"

        bashio::log.info "Exporting ${MOUNT_PATH} to ${NETWORK} (${OPTIONS})..."
        EXPORT_LINE="${MOUNT_PATH}"
        IFS=',' read -ra NETWORKS <<< "${NETWORK}"
        for net in "${NETWORKS[@]}"; do
            net=$(echo "${net}" | tr -d ' ')
            EXPORT_LINE="${EXPORT_LINE} ${net}(${OPTIONS})"
        done
        echo "${EXPORT_LINE}" >> /etc/exports
    done
fi
cat /etc/exports

# Start unfs3 user-space NFS server in foreground
bashio::log.info "Starting unfs3 NFS server..."
exec unfsd -d -s -e /etc/exports
