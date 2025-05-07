#!/usr/bin/env bash

set -e
set -o pipefail

log() {
    echo "[GVM ADD-ON] $(date +"%Y-%m-%d %H:%M:%S") - $*"
}

# Ensure required env vars are set
: "${USERNAME:?Environment variable USERNAME not set}"
: "${PASSWORD:?Environment variable PASSWORD not set}"

log "Starting GVM (OpenVAS) add-on..."

# Setup timezone
if [ -n "$TZ" ]; then
    log "Setting timezone to $TZ"
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime
    echo "$TZ" > /etc/timezone
fi

# Initialize data directory
DATA_DIR="/data"
if [ ! -d "$DATA_DIR" ]; then
    log "Creating data directory at $DATA_DIR"
    mkdir -p "$DATA_DIR"
fi

log "Launching GVM service..."
exec /usr/local/bin/dumb-init gvm-start | tee -a "$DATA_DIR/gvm.log"
