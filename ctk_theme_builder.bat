::##############################################################################
::# Author: Clive Bostock
::#   Date: 8 Apr 2023
::#   Name: ctk_theme_builder.bat
::#  Descr: CustomTkinter Theme Builder Launcher (Windows)
::##############################################################################
@echo off
set PROG_PATH=%~dp0
set APP_ENV=%PROG_PATH%\venv
cd %PROG_PATH%
call %APP_ENV%\Scripts\activate.bat

set PYTHONPATH=%PYTHONPATH%;%PROG_PATH%

call %APP_ENV%\Scripts\activate.bat

python %PROG_PATH%\controller\ctk_theme_builder.py %1 %2 %3 %4 %5 %6
