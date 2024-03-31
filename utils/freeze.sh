##############################################################################
# Author: Clive Bostock
#   Date: 1 Dec 2022 (A Merry Christmas to one and all! :o)
#   Name: freeze.bat
#  Descr: Generates a Pyython requirements.txt file for DCCM
##############################################################################
APP_HOME=$(realpath $0)
APP_HOME=$(dirname ${APP_HOME})
APP_HOME=$(dirname ${APP_HOME})
cd ${APP_HOME}
source venv/bin/activate
pip freeze | grep -v "apt-clone" > requirements.txt
