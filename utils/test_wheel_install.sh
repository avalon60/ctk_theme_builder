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

usage() {
  cat <<'EOF'
Usage:
  ./utils/test_wheel_install.sh <python-version> [wheel-path]
  ./utils/test_wheel_install.sh -l

Examples:
  ./utils/test_wheel_install.sh 3.13.5
  ./utils/test_wheel_install.sh 3.12.0 dist/ctk_theme_builder-3.2.0-py3-none-any.whl
  ./utils/test_wheel_install.sh -l

Behavior:
  - uses pyenv for the requested Python version
  - creates a scratch virtualenv under /tmp
  - installs the selected wheel into that virtualenv
  - prints the activation command for follow-on manual testing

Wheel selection:
  - if [wheel-path] is supplied, that file is used
  - otherwise the script looks for the newest *.whl in ./dist
    and then in the current directory
EOF
}

list_wheels() {
  if [ ! -d "./dist" ]; then
    echo "No dist directory found."
    exit 1
  fi

  WHEELS=$(find ./dist -maxdepth 1 -type f -name '*.whl' | sort)
  if [ -z "${WHEELS}" ]; then
    echo "No wheel files found in ./dist."
    exit 1
  fi

  echo "Wheel files in ./dist:"
  printf '%s\n' "${WHEELS}"
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

if [ "${1:-}" = "-l" ]; then
  list_wheels
  exit 0
fi

if [ $# -lt 1 ] || [ $# -gt 2 ]; then
  usage
  exit 1
fi

if ! command -v pyenv >/dev/null 2>&1; then
  echo "ERROR: pyenv is not available on PATH."
  exit 1
fi

PYTHON_VERSION="$1"
WHEEL_PATH="${2:-}"

if ! pyenv prefix "${PYTHON_VERSION}" >/dev/null 2>&1; then
  echo "ERROR: Python ${PYTHON_VERSION} is not installed in pyenv."
  echo "Install it with: pyenv install ${PYTHON_VERSION}"
  exit 1
fi

if [ -z "${WHEEL_PATH}" ]; then
  WHEEL_PATH=$(find ./dist -maxdepth 1 -type f -name '*.whl' -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -1 | cut -d ' ' -f2-)
fi

if [ -z "${WHEEL_PATH}" ]; then
  WHEEL_PATH=$(find . -maxdepth 1 -type f -name '*.whl' -printf '%T@ %p\n' | sort -nr | head -1 | cut -d ' ' -f2-)
fi

if [ -z "${WHEEL_PATH}" ]; then
  echo "ERROR: No wheel found in ./dist or the current directory."
  echo "Build the wheel first, or pass the wheel path explicitly."
  exit 1
fi

if [ ! -f "${WHEEL_PATH}" ]; then
  echo "ERROR: Wheel not found: ${WHEEL_PATH}"
  exit 1
fi

WHEEL_PATH=$(realpath_fallback "${WHEEL_PATH}")
STAMP=$(date +%Y%m%d-%H%M%S)
SCRATCH_ROOT="/tmp/ctk-theme-builder-wheel-test-${PYTHON_VERSION}-${STAMP}"
VENV_DIR="${SCRATCH_ROOT}/venv"

mkdir -p "${SCRATCH_ROOT}"

export PYENV_VERSION="${PYTHON_VERSION}"

echo "Using pyenv Python: ${PYTHON_VERSION}"
echo "Creating scratch environment: ${VENV_DIR}"
pyenv exec python -m venv "${VENV_DIR}"

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

echo "Upgrading pip..."
python -m pip install --upgrade pip

echo "Installing wheel: ${WHEEL_PATH}"
python -m pip install "${WHEEL_PATH}"

echo
echo "Environment ready."
echo "Scratch root : ${SCRATCH_ROOT}"
echo "Virtualenv   : ${VENV_DIR}"
echo
echo "Activate it with:"
echo "  source ${VENV_DIR}/bin/activate"
echo
echo "Installed package summary:"
python -m pip show ctk-theme-builder || true
