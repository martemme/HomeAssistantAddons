#!/usr/bin/env bash
# git_push_repo.sh <gitea_user> <gitea_base_url>
#
# Committa repository.json (se modificato) e lo pusha su main.
# Il messaggio include [skip ci] per evitare loop webhook.
#
# Variabili d'ambiente richieste:
#   GITEA_PUSH_PSW   — password/token Gitea (iniettata da withCredentials)

set -euo pipefail

GITEA_USER=${1:?Uso: git_push_repo.sh <gitea_user> <gitea_base_url>}
GITEA_BASE_URL=${2:?Uso: git_push_repo.sh <gitea_user> <gitea_base_url>}
GITEA_PSW=${GITEA_PUSH_PSW:?GITEA_PUSH_PSW non impostata}

git config user.email "jenkins@pipelines.mt-home.uk"
git config user.name  "Jenkins CI"

git add repository.json

if git diff --staged --quiet; then
    echo "[INFO] Nessuna modifica a repository.json — niente da committare"
    exit 0
fi

git commit -m "chore: update repository.json [skip ci]"

# Rimuove schema (https://) per costruire l'URL con credenziali
GITEA_HOST=${GITEA_BASE_URL#https://}
GITEA_HOST=${GITEA_HOST#http://}

git push \
    "https://oauth2:${GITEA_PSW}@${GITEA_HOST}/${GITEA_USER}/HomeAssistantAddons.git" \
    HEAD:main

echo "[OK] repository.json pushato su main"
