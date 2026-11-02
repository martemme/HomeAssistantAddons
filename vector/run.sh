#!/usr/bin/env bash
# shellcheck shell=bash
set -Eeuo pipefail

readonly OPTIONS_FILE="/data/options.json"
readonly VECTOR_TEMPLATE="/etc/vector/vector.yaml"
readonly CONFIG_DIR="/run/vector"
readonly CONFIG_FILE="${CONFIG_DIR}/vector.yaml"

fail() {
    echo "[ERROR] $*" >&2
    exit 1
}

[[ -x /usr/local/bin/vector ]] || fail "Vector binary is missing."
command -v journalctl >/dev/null 2>&1 || fail "journalctl is required to read the HAOS journal."
[[ -f "${OPTIONS_FILE}" ]] || fail "Supervisor options file ${OPTIONS_FILE} is missing."
[[ -f "${VECTOR_TEMPLATE}" ]] || fail "Vector configuration template ${VECTOR_TEMPLATE} is missing."

VICTORIALOGS_URL="$(jq -er '.victorialogs_url' "${OPTIONS_FILE}")" \
    || fail "victorialogs_url must be configured."
HOST_LABEL="$(jq -er '.host_label' "${OPTIONS_FILE}")" \
    || fail "host_label must be configured."

while [[ "${VICTORIALOGS_URL}" == */ ]]; do
    VICTORIALOGS_URL="${VICTORIALOGS_URL%/}"
done

if [[ ! "${VICTORIALOGS_URL}" =~ ^https?://([A-Za-z0-9.-]+|\[[0-9A-Fa-f:.]+\])(:([0-9]{1,5}))?$ ]]; then
    fail "victorialogs_url must be an HTTP(S) base URL without credentials, path, query, or fragment."
fi

if [[ -n "${BASH_REMATCH[3]:-}" ]]; then
    port=$((10#${BASH_REMATCH[3]}))
    (( port >= 1 && port <= 65535 )) || fail "victorialogs_url has an invalid port."
fi

[[ "${HOST_LABEL}" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,62}$ ]] \
    || fail "host_label may contain only letters, digits, dot, underscore, and hyphen."

JOURNAL_DIRECTORY=""
journal_files_found=false
for candidate in /var/log/journal /run/log/journal; do
    if [[ -d "${candidate}" ]] && find "${candidate}" -type f -name '*.journal' -print -quit 2>/dev/null | grep -q .; then
        JOURNAL_DIRECTORY="${candidate}"
        journal_files_found=true
        break
    fi
done

if [[ -z "${JOURNAL_DIRECTORY}" ]]; then
    for candidate in /var/log/journal /run/log/journal; do
        if [[ -d "${candidate}" ]]; then
            JOURNAL_DIRECTORY="${candidate}"
            break
        fi
    done
fi

[[ -n "${JOURNAL_DIRECTORY}" ]] || fail "No journald directory is mounted; enable journald: true in config.yaml."
if [[ "${journal_files_found}" != true ]]; then
    echo "[WARN] No journal files found in ${JOURNAL_DIRECTORY}; verify the Supervisor journald mount." >&2
fi

mkdir -p "${CONFIG_DIR}" /data/vector
sed \
    -e "s|http://victorialogs.local:9428|${VICTORIALOGS_URL}|g" \
    -e "s|__JOURNAL_DIRECTORY__|${JOURNAL_DIRECTORY}|g" \
    -e "s|__HOST_LABEL__|${HOST_LABEL}|g" \
    "${VECTOR_TEMPLATE}" > "${CONFIG_FILE}"
chmod 0600 "${CONFIG_FILE}"

/usr/local/bin/vector validate --no-environment "${CONFIG_FILE}"
exec /usr/local/bin/vector --config "${CONFIG_FILE}"
