#!/usr/bin/env bashio

# Build /etc/exports from configured shares
bashio::log.info "Configuring NFS exports..."
> /etc/exports

for index in $(bashio::config 'shares|keys[]'); do
    FOLDER=$(bashio::config "shares[${index}].folder")
    NETWORK=$(bashio::config "shares[${index}].allowed_network")
    READ_ONLY=$(bashio::config "shares[${index}].read_only")
    MOUNT_PATH="/${FOLDER}"

    if bashio::var.true "${READ_ONLY}"; then
        OPTIONS="ro,no_root_squash"
    else
        OPTIONS="rw,no_root_squash"
    fi

    bashio::log.info "Exporting ${MOUNT_PATH} to ${NETWORK} (${OPTIONS})..."
    echo "${MOUNT_PATH} ${NETWORK}(${OPTIONS})" >> /etc/exports
done

cat /etc/exports

# Start unfs3 user-space NFS server in foreground
bashio::log.info "Starting unfs3 NFS server..."
exec unfsd -d -e /etc/exports
