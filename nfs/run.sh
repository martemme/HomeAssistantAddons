#!/usr/bin/env bashio

# Read config
NETWORK=$(bashio::config 'allowed_network')

# Setup exports
bashio::log.info "Exporting /media folder to ${NETWORK}..."
echo "/media ${NETWORK}(rw,sync,no_subtree_check,no_root_squash)" > /etc/exports
cat /etc/exports

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