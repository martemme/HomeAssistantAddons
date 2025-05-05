#!/usr/bin/env bash
set -e
echo "[DEBUG] Run script started"

CONFIG="/data/options.json"

# Config via HA options
ACCESS_KEY=$(jq -r .access_key  "$CONFIG")
SECRET_KEY=$(jq -r .secret_key  "$CONFIG")
REGION=$(jq -r .region       "$CONFIG")
BUCKET=$(jq -r .bucket       "$CONFIG")


# Config via env vars (for docker container)
export MINIO_ROOT_USER="$ACCESS_KEY"
export MINIO_ROOT_PASSWORD="$SECRET_KEY"
export MINIO_REGION="${REGION:-us-east-1}"


# TLS support (optional, autodetect)
CERT_PATH="/ssl/cert.pem"
KEY_PATH="/ssl/key.pem"

# First-run: make sure bucket exists (done via client)
DATA_DIR="/data/$BUCKET"
mkdir -p "$DATA_DIR"

echo "[INFO] Starting MinIO (user: $MINIO_ROOT_USER, region: $MINIO_REGION, bucket: $BUCKET)"

if [[ -f "$CERT_PATH" && -f "$KEY_PATH" ]]; then
  echo "[INFO] TLS cert found, launching in HTTPS mode"
  exec minio server "$DATA_DIR" \
       --address ":9000" \
       --console-address ":9001" \
       --certs-dir /ssl
else
  echo "[INFO] Launching in HTTP mode"
  exec minio server "$DATA_DIR" \
       --address ":9000" \
       --console-address ":9001"
fi