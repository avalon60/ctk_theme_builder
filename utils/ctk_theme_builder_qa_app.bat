::##############################################################################
::# Author: Clive Bostock
::#   Date: 10 June 2023
::#   Name: ctk_theme_builder_test_app.bat
::#  Descr:CustomTkinter Theme Builder Test App Launcher  (Windows)
::##############################################################################
@echo off
:: Get the directory of the batch script
set PROG_PATH=%~dp0

:: Derive the parent directory of PROG_PATH
for %%I in ("%PROG_PATH%\..") do set "APP_HOME=%%~fI"

set APP_ENV=%APP_HOME%\venv
set PYTHONPATH=%PYTHONPATH%;%APP_HOME%\utils;%APP_HOME%\model;%APP_HOME%\view

call %APP_ENV%\Scripts\activate.bat
%APP_HOME%\utils\ctk_theme_builder_qa_app.py %1 %2 %3 %4 %5 %6
