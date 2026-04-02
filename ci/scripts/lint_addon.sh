#!/usr/bin/env bash
# lint_addon.sh <addon_dir>
#
# Esegue tre check su un addon HA:
#   1. hadolint    — Dockerfile best practices
#   2. yaml/json   — config.yaml o config.json valido
#   3. shellcheck  — tutti gli *.sh nella directory
#
# Esce con codice 0 se tutti i check passano, 1 altrimenti.

set -euo pipefail

ADDON=${1:?Uso: lint_addon.sh <addon_dir>}

echo "[INFO] === Lint: ${ADDON} ==="

# ── 1. hadolint ────────────────────────────────────────────────────────────────
echo "[INFO] hadolint: ${ADDON}/Dockerfile"
docker run --rm -i hadolint/hadolint < "${ADDON}/Dockerfile"

# ── 2. Config valida ───────────────────────────────────────────────────────────
if [ -f "${ADDON}/config.yaml" ]; then
    python3 -c "import yaml,sys; yaml.safe_load(open(sys.argv[1]))" "${ADDON}/config.yaml"
    echo "[OK]   ${ADDON}/config.yaml valido"
elif [ -f "${ADDON}/config.json" ]; then
    python3 -c "import json,sys; json.load(open(sys.argv[1]))" "${ADDON}/config.json"
    echo "[OK]   ${ADDON}/config.json valido"
else
    echo "[WARN] Nessuna config trovata in ${ADDON}/"
fi

# ── 3. shellcheck ──────────────────────────────────────────────────────────────
find "${ADDON}/" -name '*.sh' | while read -r f; do
    echo "[INFO] shellcheck: ${f}"
    docker run --rm -v "$PWD:/mnt" koalaman/shellcheck:stable "/mnt/${f}"
done

echo "[OK]   ${ADDON}: lint completato"
