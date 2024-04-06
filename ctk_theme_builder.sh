#!/usr/bin/env bash
##############################################################################
# Author: Clive Bostock
#   Date: 8 Apr 2023
#   Name: ctk_theme_builder.sh
#  Descr: CustomTkinter Theme Builder Launcher (Linux/Mac)
##############################################################################
PROG=$(basename $0)
PROG_DIR=$(dirname $0)
APP_HOME=$(realpath  ${PROG_DIR})

APP_ENV=${APP_HOME}/venv
APP_UTILS=${APP_HOME}/utils
APP_MODEL=${APP_HOME}/model
APP_VIEW=${APP_HOME}/view
APP_CTL=${APP_HOME}/controller

export PYTHONPATH=${PYTHONPATH}:${APP_HOME}

if [[ "${PROG}" != *\.py ]]
then
  if [[ "${PROG}" == *\.sh ]]
  then
    THEME_BUILDER_PY="${APP_CTL}/$(echo ${PROG} | sed 's/.sh/.py/')"
  else
    THEME_BUILDER_PY="${APP_CTL}/${PROG}.py"
  fi
else
  THEME_BUILDER_PY="${FULL_PATH}.py"
fi

echo "Application Home: $APP_HOME"

if [ -f ${APP_ENV}/bin/activate ]
then
  source ${APP_ENV}/bin/activate
elif [ -f ${APP_ENV}/Scripts/activate ]
then
  source ${APP_ENV}/Scripts/activate
fi

type python > /dev/null
if [ $? -eq 0 ]
then
  PYTHON="python"
else
  type python3 > /dev/null
  if [ $? -eq 0 ]
  then
    PYTHON="python3"
  else
    echo -e "Cannot find a Python interpreter. Please ensure that you have Python installed and that it can be found via \$PATH"
    exit 1
  fi
fi
${PYTHON} ${THEME_BUILDER_PY} $*