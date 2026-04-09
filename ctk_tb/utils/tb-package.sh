#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(realpath "$(dirname "$0")")
exec "${SCRIPT_DIR}/package.sh" "$@"
