::##############################################################################
::# Author: Clive Bostock
::#   Date: 10 June 2023
::#   Name: ctk_theme_builder_test_app.bat
::#  Descr:CustomTkinter Theme Builder Test App Launcher  (Windows)
::##############################################################################
@echo off
set PROG_PATH="%~dp0"
set APP_ENV=%PROG_PATH%\venv
call %APP_ENV%\Scripts\activate.bat
%PROG_PATH%\ctk_theme_builder_qa_app.py %1 %2 %3 %4 %5 %6
