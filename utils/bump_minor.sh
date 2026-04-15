#!/usr/bin/env bash
set -euo pipefail

realpath_fallback() {
  if command -v realpath >/dev/null 2>&1; then
    realpath "$1"
  elif command -v readlink >/dev/null 2>&1; then
    readlink -f "$1"
  else
    cd "$(dirname "$1")" && pwd
  fi
}

PROG_PATH=$(realpath_fallback "$0")
PROG_DIR=$(dirname "${PROG_PATH}")
APP_HOME=$(dirname "${PROG_DIR}")
PYPROJECT_FILE="${APP_HOME}/pyproject.toml"

pyproject_version() {
  grep '^version = ' "${PYPROJECT_FILE}" | head -1 | cut -f2 -d "=" | tr -d ' "'
}

cd "${APP_HOME}"

if [ "${1:-}" = "dirty" ]; then
  poetry run bump2version --allow-dirty --no-commit minor
else
  poetry run bump2version minor
fi

echo "New version: $(pyproject_version)"
