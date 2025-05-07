#!/usr/bin/env bash

set -e
set -o pipefail

log() {
    echo "[GVM ADD-ON] $(date +"%Y-%m-%d %H:%M:%S") - $*"
}

# Path to options provided by Home Assistant
CONFIG_PATH="/data/options.json"

if [ ! -f "$CONFIG_PATH" ]; then
    log "ERROR: Config file not found at $CONFIG_PATH"
    exit 1
fi

# Read variables from options.json
USERNAME=$(jq -r '.username' "$CONFIG_PATH")
PASSWORD=$(jq -r '.password' "$CONFIG_PATH")
TZ=$(jq -r '.TZ // empty' "$CONFIG_PATH")
DB_PASSWORD=$(jq -r '.DB_PASSWORD // empty' "$CONFIG_PATH")
HTTPS=$(jq -r '.HTTPS // "false"' "$CONFIG_PATH")
SSHD=$(jq -r '.SSHD // "true"' "$CONFIG_PATH")

# Validate
if [ -z "$USERNAME" ] || [ -z "$PASSWORD" ]; then
    log "ERROR: username and/or password not set in options.json"
    exit 1
fi

# Export variables for GVM
export USERNAME
export PASSWORD
export DB_PASSWORD
export TZ
export HTTPS
export SSHD

log "INFO: Starting GVM (OpenVAS) add-on as user '$USERNAME'"

# Set timezone if available
if [ -n "$TZ" ]; then
    log "INFO: Setting timezone to $TZ"
    ln -snf "/usr/share/zoneinfo/$TZ" /etc/localtime
    echo "$TZ" > /etc/timezone
fi

# Initialize data directory
DATA_DIR="/data"
if [ ! -d "$DATA_DIR" ]; then
    log "INFO: Creating data directory at $DATA_DIR"
    mkdir -p "$DATA_DIR"
fi

log "INFO: Launching GVM service..."
exec gvm-start | tee -a "$DATA_DIR/gvm.log"
