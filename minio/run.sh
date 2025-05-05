#!/usr/bin/env bash
set -e
echo "[DEBUG] Run script started"

CONFIG="/data/options.json"

# Extract config values from the JSON file
# The file is created by the Home Assistant Add-on system
# and contains the configuration options defined in the add-on config.json file
# The jq command is used to parse the JSON file and extract the values
ACCESS_KEY=$(jq -r .access_key  "$CONFIG")
SECRET_KEY=$(jq -r .secret_key  "$CONFIG")
REGION=$(jq -r .region       "$CONFIG")
BUCKET=$(jq -r .bucket       "$CONFIG")


# Configure MinIO environment variables
# These variables are used to set up the MinIO server
# The ACCESS_KEY and SECRET_KEY are used for authentication
# The REGION is used to set the region for the MinIO server
# The BUCKET is the name of the bucket to be created
export MINIO_ROOT_USER="$ACCESS_KEY"
export MINIO_ROOT_PASSWORD="$SECRET_KEY"
export MINIO_REGION="${REGION:-us-east-1}"

# Check if the bucket exists, if not create it
DATA_DIR="/data/$BUCKET"
mkdir -p "$DATA_DIR"

echo "[INFO] Starting MinIO (user: $MINIO_ROOT_USER, region: $MINIO_REGION, bucket: $BUCKET)"

# Autodetect if TLS certs are present
# If they are, launch with HTTPS, otherwise use HTTP
# This is a workaround for the fact that the minio server command does not have a --tls flag
if [[ -f /ssl/cert.pem && -f /ssl/key.pem ]]; then
  echo "[INFO] TLS cert found, launching HTTPS"
  exec minio server "$DATA_DIR" \
       --address ":9000" \
       --console-address ":9001" \
       --certs-dir /ssl
else
  echo "[INFO] Launching HTTP"
  exec minio server "$DATA_DIR" \
       --address ":9000" \
       --console-address ":9001"
fi