echo "DCCM Build started..."
set PROG_PATH="%~dp0"
REM
REM Check if the venv directory exists
if exist "%PROG_PATH%\venv" (
    echo Removing deprecated venv directory.
    rmdir /s /q "%PROG_PATH%\venv"
)

py -m venv .venv
set APP_ENV=%PROG_PATH%\.venv
call %APP_ENV%\Scripts\activate.bat
pip install virtualenv
.\.venv\Scripts\pip install -r requirements.txt
echo "Done."
