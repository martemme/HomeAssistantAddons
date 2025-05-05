#!/usr/bin/env bash
set -e
echo "[DEBUG] Run script started"

# Config via HA options
export MINIO_ROOT_USER="${access_key}"
export MINIO_ROOT_PASSWORD="${secret_key}"
export MINIO_REGION="${region:-us-east-1}"

# TLS support (optional, autodetect)
CERT_PATH="/ssl/cert.pem"
KEY_PATH="/ssl/key.pem"

# First-run: make sure bucket exists (done via client)
DATA_DIR="/data/${bucket}"
mkdir -p "$DATA_DIR"

echo "[INFO] Starting MinIO (user: $MINIO_ROOT_USER, region: $MINIO_REGION)"
if [[ -f "$CERT_PATH" && -f "$KEY_PATH" ]]; then
  echo "[INFO] TLS cert found, launching in HTTPS mode"
  exec minio server "$DATA_DIR" --address ":9000" --console-address ":9001" --certs-dir /ssl
else
  echo "[INFO] Launching in HTTP mode"
  exec minio server "$DATA_DIR" --address ":9000" --console-address ":9001"
fi
