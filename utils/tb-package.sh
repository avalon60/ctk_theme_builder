#!/usr/bin/env bash
#
# Script to package up CTk Theme Builder
#
PROG=`basename $0`
ART_CODE="ctk_theme_builder"
VERSION_FILE="model/ctk_theme_builder.py"
E="-e"
if [ ! -f "${VERSION_FILE}" ]
then
  echo $E "Unable to locate file ${VERSION_FILE}!"
  echo "Deploying chute and bailing out!"
  exit 1
fi

APP_HOME=$(realpath $0)
APP_HOME=$(dirname ${APP_HOME})
APP_HOME=$(dirname ${APP_HOME})
cd ${APP_HOME}

date_time()
{
  DATE=`date +"%Y/%m/%d %T"`
  echo $DATE
}

app_version()
{
  version=`head -30 ${VERSION_FILE} | grep "__version__" | cut -f3 -d " " |  sed 's/"//g'`
  echo "$version"
}   
display_usage()
{
  echo "Usage: ${PROG}  -v <version_tag>"
  echo $E "\nIf you don't wish to include the <artifactory-url>, <artifactory_username> and / or <artifactory_key>,"
  echo $E "on the command line, you may export them to the shell variables ARTIFACTORY_LOC, ART_USER_ID and ART_KEY"
  echo $E "respectively."
  echo $E "\nIf not supplied, the default Artifactory URL, is https://artifacthub-iad.oci.oraclecorp.com/hcgbu-dev-generic-local."
  echo $E "\nExample:"
  echo $E "\n        ./${PROG} -v 1.3.0"
  echo $E "\nThis example assumes that the ART_KEY is exported as a shell variable."
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

app_vers=`app_version`
if [ "${VERSION_TAG}" != "${app_vers}" ]
then
   echo "ERROR: A version tag of \"${VERSION_TAG}\", when ${VERSION_FILE}, thinks that it is version \"${app_vers}\""
   exit 1
fi

echo -e "Application home: ${APP_HOME}\n"
cd ${APP_HOME}
rm ${APP_HOME}/log/*.log 2> /dev/null
${APP_HOME}/utils/freeze.sh
if [ -d ../stage/ctk_theme_builder ]
then 
  rm -fr ../stage/ctk_theme_builder
fi
mkdir -p ../stage/ctk_theme_builder
for file in `cat utils/bom.lst`
do 
  cp -r $file ../stage/ctk_theme_builder
done
# Make sure we don't include the SQLite3 database.
rm ../stage/ctk_theme_builder/assets/data/*.db
cd ../stage
STAGE_LOC=`pwd`
cd ctk_theme_builder

dos2unix *.py *.txt *.sh 2> /dev/null
find assets -type f -exec dos2unix "{}" ";" 
cd user_themes
dos2unix *.json
cd ../assets
for dir in `ls -1`
do
  if [ ! -d "${dir}" ]
  then
    continue
  fi
  cd ${dir}
  dos2unix *
  cd ..
done

cd ${STAGE_LOC}
echo -e "\nWorking from : `pwd`"
find ctk_theme_builder -name "__pycache__" -exec rm -r "{}" ";" 2> /dev/null
export arch_file="${ART_CODE}-${VERSION_TAG}.zip"
echo "Creaing artifact archive:  ${arch_file}"
if [ -f ${arch_file} ]
then
  rm ${arch_file}
fi
zip -r ${arch_file} ctk_theme_builder 
if [ $? -ne 0 ]
then 
   exit 1
fi
rm -fr ../stage/ctk_theme_builder
echo -e "\nArtefact written to: ${STAGE_LOC}/${arch_file}\n"
echo "Done."
