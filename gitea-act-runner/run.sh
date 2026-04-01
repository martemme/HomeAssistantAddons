#!/usr/bin/env bash
set -e

CONFIG="/data/options.json"
ACT_RUNNER="/usr/local/bin/act_runner"
RUNNER_FILE="/data/.runner"
ACT_RUNNER_CONFIG="/data/act_runner_config.yaml"

echo "[INFO] Reading configuration from ${CONFIG}..."

GITEA_URL=$(jq -r '.gitea_url'     "$CONFIG")
RUNNER_TOKEN=$(jq -r '.runner_token'  "$CONFIG")
RUNNER_NAME=$(jq -r '.runner_name'   "$CONFIG")
RUNNER_LABELS=$(jq -r '.runner_labels' "$CONFIG")
LOG_LEVEL=$(jq -r '.log_level'     "$CONFIG")

# ------------------------------------------------------------------
# Validate required fields
# ------------------------------------------------------------------
if [[ -z "$GITEA_URL" || "$GITEA_URL" == "null" ]]; then
    echo "[ERROR] gitea_url is not configured. Set it in the addon options and restart."
    exit 1
fi

if [[ -z "$RUNNER_TOKEN" || "$RUNNER_TOKEN" == "null" ]]; then
    echo "[ERROR] runner_token is not configured. Set it in the addon options and restart."
    exit 1
fi

# ------------------------------------------------------------------
# Registration  (only on first boot — .runner persists in /data/)
# ------------------------------------------------------------------
# act_runner writes .runner into the current working directory, so
# we change into /data/ so the file ends up on the persistent volume.
cd /data

if [[ ! -f "$RUNNER_FILE" ]]; then
    echo "[INFO] Registering runner '${RUNNER_NAME}' with ${GITEA_URL}..."
    "$ACT_RUNNER" register \
        --no-interactive \
        --instance "$GITEA_URL" \
        --token    "$RUNNER_TOKEN" \
        --name     "$RUNNER_NAME" \
        --labels   "$RUNNER_LABELS"
    echo "[INFO] Registration complete. .runner saved to /data/."
else
    echo "[INFO] Runner already registered, skipping registration."
fi

# ------------------------------------------------------------------
# Generate act_runner runtime config
# ------------------------------------------------------------------
echo "[INFO] Writing act_runner config to ${ACT_RUNNER_CONFIG}..."
cat > "$ACT_RUNNER_CONFIG" <<EOF
log:
  level: ${LOG_LEVEL}

runner:
  capacity: 2

container:
  network: bridge
  valid_volumes: []

cache:
  enabled: false
EOF

# ------------------------------------------------------------------
# Start the daemon
# ------------------------------------------------------------------
echo "[INFO] Starting act_runner daemon..."
exec "$ACT_RUNNER" daemon --config "$ACT_RUNNER_CONFIG"
