#!/usr/bin/env bash
set -euo pipefail

PROG_PATH=$(realpath "$0")
PROG_DIR=$(dirname "${PROG_PATH}")
APP_HOME=$(dirname "${PROG_DIR}")
cd "${APP_HOME}"

if [ "${1:-}" = "dirty" ]; then
  poetry run bump2version --allow-dirty --no-commit patch
else
  poetry run bump2version patch
fi
