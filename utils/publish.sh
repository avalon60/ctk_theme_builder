#!/usr/bin/env bash
##############################################################################
# Author: Clive Bostock
#   Date: 10 Apr 2026
#   Name: publish.sh
#  Descr: Uploads a packaged CTk Theme Builder release to PyPI or TestPyPI.
##############################################################################
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

find_twine() {
  if command -v python >/dev/null 2>&1 && python -m twine --version >/dev/null 2>&1; then
    echo "python -m twine"
    return
  fi

  if command -v python3 >/dev/null 2>&1 && python3 -m twine --version >/dev/null 2>&1; then
    echo "python3 -m twine"
    return
  fi

  if command -v twine >/dev/null 2>&1; then
    local twine_path
    twine_path="$(command -v twine)"
    case "${twine_path}" in
      *"/.pyenv/shims/twine")
        ;;
      *)
        echo "${twine_path}"
        return
        ;;
    esac
  fi

  if command -v pyenv >/dev/null 2>&1; then
    local pyenv_root
    pyenv_root="$(pyenv root)"
    for candidate in "${pyenv_root}"/versions/*/bin/twine; do
      if [ -x "${candidate}" ]; then
        echo "${candidate}"
        return
      fi
    done
  fi
  echo ""
}

display_usage() {
  cat <<'EOF'
Usage:
  ./utils/publish.sh -v <version_tag> [-r pypi|testpypi]
  ./utils/publish.sh -V

Examples:
  ./utils/publish.sh -v 3.2.0
  ./utils/publish.sh -v 3.2.0 -r testpypi
  ./utils/publish.sh -V

Use -V to print the version from pyproject.toml.
Use -v as a safety check before upload.
EOF
  exit 1
}

PROG_PATH=$(realpath_fallback "$0")
PROG_DIR=$(dirname "${PROG_PATH}")
APP_HOME=$(dirname "${PROG_DIR}")
PYPROJECT_FILE="${APP_HOME}/pyproject.toml"
PACKAGE_INIT_FILE="${APP_HOME}/ctk_tb/model/ctk_theme_builder.py"
DIST_DIR="${APP_HOME}/dist"

while getopts "v:r:V" options; do
  case "${options}" in
    v) VERSION_TAG="${OPTARG}" ;;
    r) REPOSITORY="${OPTARG}" ;;
    V) SHOW_VERSION=Y ;;
    *) display_usage ;;
  esac
done

pyproject_version() {
  grep '^version = ' "${PYPROJECT_FILE}" | head -1 | cut -f2 -d "=" | tr -d ' "'
}

package_version() {
  grep '^__version__ = ' "${PACKAGE_INIT_FILE}" | head -1 | cut -f2 -d "=" | tr -d ' "'
}

TWINE=$(find_twine)
if [ -z "${TWINE}" ]; then
  echo "ERROR: Twine is required to publish this project."
  exit 1
fi

echo "Using Twine command: ${TWINE}"
if ! eval "${TWINE}" --version >/dev/null 2>&1; then
  echo "ERROR: Selected Twine command is not runnable: ${TWINE}"
  echo "Install Twine into the active environment, or fix the Twine shim on your PATH."
  exit 1
fi

pushd "${APP_HOME}" >/dev/null

if [ "${SHOW_VERSION:-N}" = "Y" ]; then
  pyproject_version
  popd >/dev/null
  exit 0
fi

if [ -z "${VERSION_TAG:-}" ]; then
  display_usage
fi

REPOSITORY="${REPOSITORY:-pypi}"
if [ "${REPOSITORY}" != "pypi" ] && [ "${REPOSITORY}" != "testpypi" ]; then
  echo "ERROR: Repository must be either 'pypi' or 'testpypi'."
  exit 1
fi

PYPROJECT_VERSION=$(pyproject_version)
PACKAGE_VERSION=$(package_version)

if [ "${VERSION_TAG}" != "${PYPROJECT_VERSION}" ]; then
  echo "ERROR: Version tag ${VERSION_TAG} does not match ${PYPROJECT_FILE} (${PYPROJECT_VERSION})."
  exit 1
fi

if [ "${VERSION_TAG}" != "${PACKAGE_VERSION}" ]; then
  echo "ERROR: Version tag ${VERSION_TAG} does not match ${PACKAGE_INIT_FILE} (${PACKAGE_VERSION})."
  exit 1
fi

WHEEL_FILE=$(find "${DIST_DIR}" -maxdepth 1 -type f -name "ctk_theme_builder-${VERSION_TAG}-*.whl" | head -1)
SDIST_FILE=$(find "${DIST_DIR}" -maxdepth 1 -type f -name "ctk_theme_builder-${VERSION_TAG}.tar.gz" | head -1)

if [ -z "${WHEEL_FILE}" ] || [ -z "${SDIST_FILE}" ]; then
  echo "ERROR: Expected release artefacts were not found in ${DIST_DIR}."
  echo "Build the release first with ./utils/package.sh -v ${VERSION_TAG}"
  exit 1
fi

echo "App home: ${APP_HOME}"
echo "Release version: ${VERSION_TAG}"
echo "Target repository: ${REPOSITORY}"

echo "Checking release metadata with twine..."
eval "${TWINE}" check "${WHEEL_FILE}" "${SDIST_FILE}"

echo "Uploading release artefacts..."
if [ "${REPOSITORY}" = "pypi" ]; then
  eval "${TWINE}" upload "${WHEEL_FILE}" "${SDIST_FILE}"
else
  eval "${TWINE}" upload --repository testpypi "${WHEEL_FILE}" "${SDIST_FILE}"
fi

popd >/dev/null
