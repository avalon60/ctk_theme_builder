echo "DCCM Build started..."
set PROG_PATH="%~dp0"
py -m venv venv
set APP_ENV=%PROG_PATH%\venv
call %APP_ENV%\Scripts\activate.bat
pip install virtualenv
.\venv\Scripts\pip install -r requirements.txt
echo "Done."
