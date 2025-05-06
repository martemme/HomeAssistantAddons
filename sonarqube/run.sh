#!/usr/bin/env sh
set -e

# --- Default paths se non passati via env ---
: "${DATA_PATH:=/share/sonarqube/data}"
: "${EXT_PATH:=/share/sonarqube/extensions}"
: "${TZ:=Europe/Rome}"

# --- Variabili JDBC (obbligatorie) ---
: "${SONAR_JDBC_URL:?Serve SONAR_JDBC_URL, es. jdbc:postgresql://sonarqube_db:5432/sonar}"
: "${SONAR_JDBC_USERNAME:?Serve SONAR_JDBC_USERNAME}"
: "${SONAR_JDBC_PASSWORD:?Serve SONAR_JDBC_PASSWORD}"

# --- Imposto timezone a container start ---
ln -snf "/usr/share/zoneinfo/${TZ}" /etc/localtime && echo "${TZ}" > /etc/timezone

# --- Creo e monto le cartelle host in container ---
mkdir -p "${DATA_PATH}" "${EXT_PATH}"
cd "${SONARQUBE_HOME}"

# sposto le cartelle interne originali (evt. backup)
[ -d data ]      && mv data      data.orig || true
[ -d extensions ]&& mv extensions extensions.orig || true

# link simbolici verso le cartelle condivise
ln -s "${DATA_PATH}"      data
ln -s "${EXT_PATH}"       extensions

# --- Esporto le variabili per SonarQube ---
export SONAR_JDBC_URL
export SONAR_JDBC_USERNAME
export SONAR_JDBC_PASSWORD

# --- Avvio SonarQube in foreground ---
exec "${SONARQUBE_BIN}/sonar.sh" console