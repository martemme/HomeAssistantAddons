#!/usr/bin/env bash
set -e
bashio::log.info "Run script started"

# Config via HA options
ACCESS_KEY=$(bashio::config 'access_key')
SECRET_KEY=$(bashio::config 'secret_key')
REGION=$(bashio::config 'region')
BUCKET=$(bashio::config 'bucket')

# Config via env vars (for docker container)
export MINIO_ROOT_USER="${ACCESS_KEY}"
export MINIO_ROOT_PASSWORD="${SECRET_KEY}"
export MINIO_REGION="${REGION:-us-east-1}"


# TLS support (optional, autodetect)
CERT_PATH="/ssl/cert.pem"
KEY_PATH="/ssl/key.pem"

# First-run: make sure bucket exists (done via client)
DATA_DIR="/data/${BUCKET}"
mkdir -p "${DATA_DIR}"

bashio::log.info "Starting MinIO (user: ${ACCESS_KEY}, region: ${MINIO_REGION}, bucket: ${BUCKET})"
if bashio::fs.file_exists '/ssl/cert.pem' && bashio::fs.file_exists '/ssl/key.pem'; then
  bashio::log.info "TLS cert found, launching HTTPS"
  exec minio server "${DATA_DIR}" \
       --address ":9000" \
       --console-address ":9001" \
       --certs-dir /ssl
else
  bashio::log.info "Launching HTTP"
  exec minio server "${DATA_DIR}" \
       --address ":9000" \
       --console-address ":9001"
fi