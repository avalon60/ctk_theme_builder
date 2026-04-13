#!/usr/bin/env bash
##############################################################################
# Author: Clive Bostock
#   Date: 7 Apr 2026
#   Name: package.sh
#  Descr: Build wheel-era release artefacts for CTk Theme Builder.
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

find_poetry() {
  if command -v python >/dev/null 2>&1 && python -m poetry --version >/dev/null 2>&1; then
    echo "python -m poetry"
  elif command -v python3 >/dev/null 2>&1 && python3 -m poetry --version >/dev/null 2>&1; then
    echo "python3 -m poetry"
  elif command -v poetry >/dev/null 2>&1; then
    echo "poetry"
  elif [ -x "${HOME}/.local/bin/poetry" ]; then
    echo "${HOME}/.local/bin/poetry"
  else
    echo ""
  fi
}

display_usage() {
  echo "Usage: $0 -v <version_tag>"
  echo "       $0 -V"
  echo
  echo "Example:"
  echo "  ./utils/package.sh -v 3.2.0"
  echo "  ./utils/package.sh -V"
  echo ""
  echo "Use -V to obtain the version according to $(basename ${PYPROJECT_FILE}) (authoritative truth)."
  exit 1
}

PROG_PATH=$(realpath_fallback "$0")
PROG_DIR=$(dirname "${PROG_PATH}")
APP_HOME=$(dirname "${PROG_DIR}")
PROJECT_NAME="ctk-theme-builder"
DIST_DIR="${APP_HOME}/dist"
RELEASE_DIR="${DIST_DIR}/release"
VERSION_FILE="${APP_HOME}/ctk_tb/model/ctk_theme_builder.py"
PYPROJECT_FILE="${APP_HOME}/pyproject.toml"
REQUIREMENTS_FILE="${APP_HOME}/requirements.txt"
RELEASE_GUIDE="${APP_HOME}/docs/release-artefact-guide.md"

while getopts "v:V" options; do
  case "${options}" in
    v) VERSION_TAG="${OPTARG}" ;;
    V) SHOW_VERSION=Y ;;
    *) display_usage ;;
  esac
done

POETRY=$(find_poetry)
if [ -z "${POETRY}" ]; then
  echo "ERROR: Poetry is required to package this project."
  exit 1
fi

echo "Using Poetry command: ${POETRY}"
if ! eval "${POETRY}" --version >/dev/null 2>&1; then
  echo "ERROR: Selected Poetry command is not runnable: ${POETRY}"
  echo "Install Poetry into the active environment, or fix the Poetry shim on your PATH."
  exit 1
fi

pushd "${APP_HOME}" >/dev/null

app_version() {
  grep '__version__' "${VERSION_FILE}" | head -1 | cut -f3 -d " " | tr -d '"'
}

pyproject_version() {
  grep '^version = ' "${PYPROJECT_FILE}" | head -1 | cut -f2 -d "=" | tr -d ' "'
}

if [ "${SHOW_VERSION:-N}" = "Y" ]; then
  pyproject_version
  popd >/dev/null
  exit 0
fi

if [ -z "${VERSION_TAG:-}" ]; then
  display_usage
fi

APP_VERSION=$(app_version)
PYPROJECT_VERSION=$(pyproject_version)

if [ "${VERSION_TAG}" != "${APP_VERSION}" ]; then
  echo "ERROR: Version tag ${VERSION_TAG} does not match ${VERSION_FILE} (${APP_VERSION})."
  exit 1
fi

if [ "${VERSION_TAG}" != "${PYPROJECT_VERSION}" ]; then
  echo "ERROR: Version tag ${VERSION_TAG} does not match ${PYPROJECT_FILE} (${PYPROJECT_VERSION})."
  exit 1
fi

echo "App home: ${APP_HOME}"
echo "Release version: ${VERSION_TAG}"

rm -rf "${RELEASE_DIR}"
mkdir -p "${RELEASE_DIR}"

echo "Checking Poetry metadata..."
eval "${POETRY}" check

if ! eval "${POETRY}" export --help >/dev/null 2>&1; then
  echo "ERROR: The selected Poetry installation does not provide the 'export' command."
  echo "Install the poetry-plugin-export plugin in the active environment."
  echo "Example: python -m pip install poetry-plugin-export"
  exit 1
fi

echo "Exporting requirements.txt..."
eval "${POETRY}" export --format requirements.txt --without-hashes --only main --output "${REQUIREMENTS_FILE}"

echo "Building sdist and wheel..."
eval "${POETRY}" build

WHEEL_FILE=$(find "${DIST_DIR}" -maxdepth 1 -type f -name "ctk_theme_builder-${VERSION_TAG}-*.whl" | head -1)
SDIST_FILE=$(find "${DIST_DIR}" -maxdepth 1 -type f -name "ctk_theme_builder-${VERSION_TAG}.tar.gz" | head -1)

if [ -z "${WHEEL_FILE}" ] || [ -z "${SDIST_FILE}" ]; then
  echo "ERROR: Expected build artefacts were not produced in ${DIST_DIR}."
  exit 1
fi

cp "${WHEEL_FILE}" "${RELEASE_DIR}/"
cp "${SDIST_FILE}" "${RELEASE_DIR}/"
cp "${REQUIREMENTS_FILE}" "${RELEASE_DIR}/"
cp "${RELEASE_GUIDE}" "${RELEASE_DIR}/"

pushd "${RELEASE_DIR}" >/dev/null
sha256sum "$(basename "${WHEEL_FILE}")" "$(basename "${SDIST_FILE}")" requirements.txt release-artefact-guide.md > SHA256SUMS
popd >/dev/null

ARTEFACT_ZIP="${DIST_DIR}/${PROJECT_NAME}-${VERSION_TAG}-release.zip"
rm -f "${ARTEFACT_ZIP}"

pushd "${DIST_DIR}" >/dev/null
zip -rq "$(basename "${ARTEFACT_ZIP}")" release
popd >/dev/null

echo
echo "Built artefacts:"
echo "  Wheel : ${WHEEL_FILE}"
echo "  Sdist : ${SDIST_FILE}"
echo "  Bundle: ${ARTEFACT_ZIP}"
echo
echo "Release contents staged in: ${RELEASE_DIR}"

popd >/dev/null
