##############################################################################
# Author: Clive Bostock
#   Date: 1 Dec 2022 (A Merry Christmas to one and all! :o)
#   Name: freeze.bat
#  Descr: Generates a Pyython requirements.txt file for DCCM
##############################################################################
source venv/bin/activate
pip freeze | grep -v "apt-clone" > requirements.txt
