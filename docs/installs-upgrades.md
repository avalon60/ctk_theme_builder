# Requirements

You must have Python installed. CTk Theme Builder supports Python 3.10 through Python 3.13. Python 3.12 is a good default choice.

The application has been tested against Python 3.12.

The application has been tested on Linux Mint and Windows 11.

macOS is expected to work, but the current wheel-based deployment flow has not yet been validated there.

There is no obvious reason as to why the application should not work on other Linux distributions.

You will require around 160MB of disk space.

## Ubuntu Based Linux Distributions

For Ubuntu based distros (for example Linux Mint, Elementary OS and Zorin OS), please ensure that the `venv` package is installed for the Python version you intend to use. For example:

`apt install python3.12-venv`

## Installation

CTk Theme Builder is now installed as a Python package. The preferred deployment modes are:

- install from PyPI with `pip`
- install from a downloaded wheel

The installed application command is:

`ctk-theme-builder`

## Install From PyPI

If the package has been published to PyPI, install it with:

`python -m pip install ctk-theme-builder`

If your platform prefers `python3`, use:

`python3 -m pip install ctk-theme-builder`

## Install From A Wheel

If you have downloaded a wheel artefact, install it with:

`python -m pip install ctk_theme_builder-3.2.0-py3-none-any.whl`

Adjust the filename to match the version you downloaded.

## Upgrades

Upgrade an existing installation with:

`python -m pip install --upgrade ctk-theme-builder`

Or, when installing from a wheel:

`python -m pip install --upgrade ctk_theme_builder-3.2.0-py3-none-any.whl`

## Launching CTk Theme Builder

Once installed, launch the application from a terminal or command prompt with:

`ctk-theme-builder`

This command is provided by the Python environment into which the package was installed.

## User Data Location

CTk Theme Builder now keeps mutable user data outside the install location.

The default user data home is:

`~/CTkThemeBuilder`

This contains the working directories for:

- themes
- palettes
- logs
- temporary files
- application state, including the SQLite database

## Migrating Themes And Palettes From An Older Install

If you are moving from an older directory-based installation, use:

`ctktb-migrate-assets <old-install-root>`

Example:

`ctktb-migrate-assets /home/clive/utilities/ctk_theme_builder`

The migration command:

- inspects the old install database to find the legacy theme location
- copies only themes that do not already exist in your current user-data theme folder
- copies matching palette files for each newly copied theme
- reports which themes were copied and which were skipped

## PATH

If `ctk-theme-builder` is not found, the Python environment's scripts directory may not be on your `PATH`.

Typical fixes are:

- activate the virtual environment before launching
- install into an environment that already exposes scripts on your `PATH`
- use `pipx` if you want the command exposed as a standalone user tool

## Desktop Launchers And Shortcuts

Desktop launchers and shortcuts are still possible, but they should now target the installed command rather than old repo-local `.sh` or `.bat` wrapper scripts.

Use one of these approaches:

- Linux desktop launcher: set the command to `ctk-theme-builder`
- Windows shortcut: point to the `ctk-theme-builder` launcher created in the Python environment's `Scripts` directory
- macOS launcher: create a launcher that runs `ctk-theme-builder` from the environment where it was installed

If you install into a virtual environment, the launcher or shortcut must target the command from that same environment.
