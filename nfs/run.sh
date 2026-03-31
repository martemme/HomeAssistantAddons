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
        OPTIONS="ro,sync,no_subtree_check,no_root_squash"
    else
        OPTIONS="rw,sync,no_subtree_check,no_root_squash"
    fi

    bashio::log.info "Exporting ${MOUNT_PATH} to ${NETWORK} (${OPTIONS})..."
    echo "${MOUNT_PATH} ${NETWORK}(${OPTIONS})" >> /etc/exports
done

cat /etc/exports

# Load NFS kernel module
bashio::log.info "Loading nfsd kernel module..."
modprobe nfsd 2>/dev/null || bashio::log.warning "nfsd module not available, assuming built-in..."

# Mount nfsd filesystem if not already mounted
if ! mountpoint -q /proc/fs/nfsd 2>/dev/null; then
    bashio::log.info "Mounting nfsd filesystem..."
    mount -t nfsd nfsd /proc/fs/nfsd || bashio::log.warning "Could not mount nfsd filesystem, it may be built-in..."
fi

# Start NFS services
bashio::log.info "Starting NFS services..."
rpcbind
exportfs -ra

# Start rpc.statd for file locking
rpc.statd &

# Start the NFS server kernel threads
rpc.nfsd

# Start rpc.mountd in the foreground to keep the container running
exec rpc.mountd --no-udp -F
