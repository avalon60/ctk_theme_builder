::##############################################################################
::# Author: Clive Bostock
::#   Date: 1 Dec 2022 (A Merry Christmas to one and all! :o)
::#   Name: dccm.sh
::#  Descr: CustomTkinter, V4 -> V5, Theme file migrator
::##############################################################################
@echo off
set PROG_PATH="%~dp0"
set APP_ENV=%PROG_PATH%\venv
call %APP_ENV%\Scripts\activate.bat
%PROG_PATH%\ctk_theme_migrate.py %1 %2 %3 %4 %5 %6
