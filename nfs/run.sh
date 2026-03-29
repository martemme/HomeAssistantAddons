#!/usr/bin/env bashio

# Read config
NETWORK=$(bashio::config 'allowed_network')

# Setup exports
bashio::log.info "Exporting /media folder to ${NETWORK}..."
echo "/media ${NETWORK}(rw,sync,no_subtree_check,no_root_squash)" > /etc/exports
cat /etc/exports

# Load NFS kernel module
bashio::log.info "Loading nfsd kernel module..."
modprobe nfsd 2>/dev/null || bashio::log.warning "nfsd module not available, assuming built-in..."

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