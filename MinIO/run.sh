#!/usr/bin/env bash
set -e

# Config via HA options
export MINIO_ROOT_USER="${ACCESS_KEY}"
export MINIO_ROOT_PASSWORD="${SECRET_KEY}"
export MINIO_REGION="${REGION:-us-east-1}"

# TLS support (optional, autodetect)
CERT_PATH="/ssl/cert.pem"
KEY_PATH="/ssl/key.pem"

# Data path
DATA_DIR="/data"

# First-run: make sure bucket exists (done via client)
BUCKET="${BUCKET}"
mkdir -p "$DATA_DIR/$BUCKET"

echo "[INFO] Starting MinIO with access: $ACCESS_KEY, region: $MINIO_REGION"
if [[ -f "$CERT_PATH" && -f "$KEY_PATH" ]]; then
  echo "[INFO] TLS cert found, starting in HTTPS mode"
  exec minio server $DATA_DIR --address ":9000" --console-address ":9001" --certs-dir /ssl
else
  echo "[INFO] Starting in HTTP mode"
  exec minio server $DATA_DIR --address ":9000" --console-address ":9001"
fi
