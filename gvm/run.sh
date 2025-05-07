#!/usr/bin/env bash

set -e
set -o pipefail

log() {
    echo "[GVM ADD-ON] $(date +"%Y-%m-%d %H:%M:%S") - $*"
}

# Load user config passed by Home Assistant (as JSON env vars)
CONFIG_PATH="/data/options.json"

if [ ! -f "$CONFIG_PATH" ]; then
    log "ERROR: Config file not found at $CONFIG_PATH"
    exit 1
fi

# Extract variables using jq
USERNAME=$(jq -r '.username' "$CONFIG_PATH")
PASSWORD=$(jq -r '.password' "$CONFIG_PATH")

# Validate
if [ -z "$USERNAME" ] || [ -z "$PASSWORD" ]; then
    log "ERROR: username and/or password not set in options.json"
    exit 1
fi

# Set them for the environment
export USERNAME
export PASSWORD
export DB_PASSWORD="$PASSWORD"

log "INFO: Starting GVM (OpenVAS) add-on as user $USERNAME..."

# Setup timezone
if [ -n "$TZ" ]; then
    log "INFO: Setting timezone to $TZ"
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime
    echo "$TZ" > /etc/timezone
fi

# Initialize data directory
DATA_DIR="/data"
if [ ! -d "$DATA_DIR" ]; then
    log "INFO: Creating data directory at $DATA_DIR"
    mkdir -p "$DATA_DIR"
fi

log "INFO: Launching GVM service..."
exec /usr/local/bin/dumb-init gvm-start | tee -a "$DATA_DIR/gvm.log"
