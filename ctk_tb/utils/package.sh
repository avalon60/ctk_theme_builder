#!/usr/bin/env bash
#
# Script to package up CTk Theme Builder
#
set -euo pipefail

PROG=$(basename "$0")
ART_CODE="ctk_theme_builder"
VERSION_FILE="model/ctk_theme_builder.py"

if [ ! -f "${VERSION_FILE}" ]
then
  echo "Unable to locate file ${VERSION_FILE}!"
  echo "Deploying chute and bailing out!"
  exit 1
fi

APP_HOME=$(realpath "$0")
APP_HOME=$(dirname "${APP_HOME}")
APP_HOME=$(dirname "${APP_HOME}")
cd "${APP_HOME}"

app_version()
{
  head -30 "${VERSION_FILE}" | grep "__version__" | cut -f3 -d " " | sed 's/"//g'
}

export_requirements()
{
  if command -v poetry >/dev/null 2>&1
  then
    POETRY_CMD=(poetry)
  elif [ -x "${HOME}/.local/bin/poetry" ]
  then
    POETRY_CMD=("${HOME}/.local/bin/poetry")
  else
    POETRY_CMD=()
  fi

  if [ ${#POETRY_CMD[@]} -eq 0 ]
  then
    echo "ERROR: Poetry is required on the build system to export requirements.txt."
    echo "Install Poetry and rerun ${PROG}."
    exit 1
  fi

  echo "Exporting requirements.txt from Poetry lock data..."
  "${POETRY_CMD[@]}" export --format requirements.txt --without-hashes --output requirements.txt
}

display_usage()
{
  echo "Usage: ${PROG} -v <version_tag>"
  echo
  echo "Example:"
  echo "  ./${PROG} -v 3.1.0"
  exit
}

while getopts "v:l" options;
do
  case $options in
    v) VERSION_TAG=${OPTARG};;
    l) WRITE_LOG=Y;;
    *) display_usage;
       exit 1;;
   \?) display_usage;
       exit 1;;
  esac
done

app_vers=$(app_version)
if [ "${VERSION_TAG:-}" != "${app_vers}" ]
then
  echo "ERROR: A version tag of \"${VERSION_TAG:-}\", when ${VERSION_FILE}, thinks that it is version \"${app_vers}\""
  exit 1
fi

echo -e "Application home: ${APP_HOME}\n"
cd "${APP_HOME}"
rm "${APP_HOME}"/log/*.log 2> /dev/null || true
export_requirements

if [ -d ../stage/ctk_theme_builder ]
then
  rm -fr ../stage/ctk_theme_builder
fi
mkdir -p ../stage/ctk_theme_builder
while IFS= read -r file
do
  cp -r "$file" ../stage/ctk_theme_builder
done < utils/bom.lst

# Make sure we don't include the SQLite3 database.
rm -f ../stage/ctk_theme_builder/assets/data/*.db
cd ../stage
STAGE_LOC=$(pwd)
cd ctk_theme_builder

dos2unix *.py *.txt *.sh 2> /dev/null || true
find assets -type f -exec dos2unix "{}" ";" 2> /dev/null || true

cd user_themes
dos2unix *.json 2> /dev/null || true
cd ../assets
for dir in *
do
  if [ ! -d "${dir}" ]
  then
    continue
  fi
  cd "${dir}"
  dos2unix * 2> /dev/null || true
  cd ..
done

cd "${STAGE_LOC}"
echo -e "\nWorking from : $(pwd)"
find ctk_theme_builder -name "__pycache__" -exec rm -r "{}" ";" 2> /dev/null || true
arch_file="${ART_CODE}-${VERSION_TAG}.zip"
echo "Creating artifact archive: ${arch_file}"
if [ -f "${arch_file}" ]
then
  rm "${arch_file}"
fi
zip -r "${arch_file}" ctk_theme_builder
rm -fr ../stage/ctk_theme_builder
echo -e "\nArtefact written to: ${STAGE_LOC}/${arch_file}\n"
echo "Done."
