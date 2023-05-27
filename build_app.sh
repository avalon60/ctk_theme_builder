#!/usr/bin/env bash
##############################################################################
# Author: Clive Bostock
#   Date: 3 Apr 2023
#   Name: build_app.sh
#  Descr: Setup Python environment and modules for Ctk Theme Builder
##############################################################################
fix_eols ()
{
  echo "Ensuring Linux style line terminators."
  for file in `ls *.sh *.py *.md 2> /dev/null`
  do
   cp ${file} ${file}.edit
   echo "Converting EOL for file ${file}"
   cat ${file}.edit |  tr -d '\r' > ${file}
   rm  ${file}.edit
  done
  asset_dirs="config etc palettes themes views"
  for dir in $asset_dirs
  do 
    cd assets/${dir}
    echo "Processing assets/${DIR}..."
    for file in `ls *.ini *.json 2> /dev/null`
    do
     cp ${file} ${file}.edit
     echo "Converting EOL for file ${file}"
     cat ${file}.edit |  tr -d '\r' > ${file}
     rm  ${file}.edit
    done
    cd ../..
  done
  echo "Line terminators converted."
}
echo "CTK Theme Builder build started..."
fix_eols

PROG_PATH=`dirname $0`
python3 -m venv venv
APP_ENV=${PROG_PATH}/venv
source ${APP_ENV}/bin/activate
python get-pip.py
${APP_ENV}/bin/pip install -r requirements.txt
if [ ! -f "ctk_theme_builder" ]
then
  echo "Hard linking ctk_theme_builder.sh to ctk_theme_builder"
  ln ctk_theme_builder.sh ctk_theme_builder
  chmod 750 ctk_theme_builder
  echo "Linked."
fi

echo "App build done."
