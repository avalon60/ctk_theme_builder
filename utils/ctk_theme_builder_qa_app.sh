#!/usr/bin/env bash
##############################################################################
# Author: Clive Bostock
#   Date: 10 June 2023
#   Name: ctk_theme_builder_test_app.sh
#  Descr: CustomTkinter Theme Builder Test App Launcher (Linux/Mac)
##############################################################################
PROG=$(basename $0)
PROG_DIR=$(dirname $0)
APP_HOME=$(realpath  ${PROG_DIR})
APP_HOME=$(dirname ${APP_HOME})
APP_ENV=${APP_HOME}/venv
APP_UTILS=${APP_HOME}/utils
APP_MODEL=${APP_HOME}/model
APP_VIEW=${APP_HOME}/view

export PYTHONPATH=${PYTHONPATH}:${APP_UTILS}:${APP_MODEL}:${APP_VIEW}

if [[ "${PROG}" == *\.sh ]]
then
  QA_PY="${APP_UTILS}/$(echo ${PROG} | sed 's/.sh/.py/')"
else
  QA_PY="${FULL_PATH}.py"
fi


if [ -f ${APP_ENV}/bin/activate ]
then
  source ${APP_ENV}/bin/activate
elif [ -f ${APP_ENV}/Scripts/activate ]
then
  source ${APP_ENV}/Scripts/activate
fi 
type python 2> /dev/null
if [ $? -eq 0 ]
then
  PYTHON="python"
else
  type python3 2> /dev/null
  if [ $? -eq 0 ]
  then
    PYTHON="python3"
  else
    echo -e "Cannot find a Python interpreter. Please ensure that you have Python installed and that it can be found via \$PATH"
    exit 1
  fi
fi

${PYTHON} ${QA_PY} $*