# Installation, Upgrade, And Migration Notes

![CTk Theme Builder](./ctk-tb-logo.png)

CTk Theme Builder supports Python 3.10 through Python 3.13.

The main installation guidance now lives in the [README](../README.md). This note is for the parts that are more operational:

- upgrading an existing installation
- installing from a wheel artefact
- migrating data from an older directory-based install
- troubleshooting PATH and launcher issues

## Requirements

- Python 3.10 to 3.13
- a desktop environment capable of running Tk-based GUI applications

For Ubuntu-based distributions, ensure that the `venv` package is installed for the Python version you intend to use. For example:

`apt install python3.12-venv`

## Upgrade From PyPI

Upgrade an existing installation with:

`python -m pip install --upgrade ctk-theme-builder`

If your platform prefers `python3`, use:

`python3 -m pip install --upgrade ctk-theme-builder`

After upgrading, launch the application with:

`ctk-theme-builder`

## Install Or Upgrade From A Wheel

If you have downloaded a wheel artefact, install or upgrade it with:

`python -m pip install --upgrade ctk_theme_builder-<version>-py3-none-any.whl`

Replace `<version>` with the wheel version you downloaded.

After installation, launch the application with:

`ctk-theme-builder`

## User Data Location

CTk Theme Builder keeps mutable user data outside the install location.

The default user data home is:

`~/CTkThemeBuilder`

This contains the working directories for:

- themes
- palettes
- logs
- temporary files
- application state, including the SQLite database

This means package upgrades do not normally need to rewrite or relocate your working themes and palettes.

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
- use `uvx --from ctk-theme-builder ctk-theme-builder` if you prefer a tool-managed run path

## Desktop Launchers And Shortcuts

Desktop launchers and shortcuts can be created in a few different ways, depending on how you run CTk Theme Builder.

For an installed package, the preferred target is the installed command:

- Linux desktop launcher: set the command to `ctk-theme-builder`
- Windows shortcut: point to the `ctk-theme-builder` launcher created in the Python environment's `Scripts` directory
- macOS launcher: create a launcher that runs `ctk-theme-builder` from the environment where it was installed

If you install into a virtual environment, the launcher or shortcut must target the command from that same environment.

On Linux, installing from a wheel or via `pip` may also create an application menu entry automatically, depending on the desktop environment and how the Python environment exposes desktop integration.

If you prefer not to deal with virtual-environment activation manually, CTk Theme Builder can also generate a convenience launcher for the current environment from:

`Tools -> Generate Launcher`

This writes a platform-specific launcher into:

`~/CTkThemeBuilder/launchers`

The generated launcher uses the interpreter from the currently running CTk Theme Builder session, so it is a practical way to create a clickable shortcut for the exact environment you are using.

On Linux, the launcher generation step creates:

- `ctk-theme-builder.sh` as the runner script
- `ctk-theme-builder.desktop` as the desktop-entry file

From the launcher result dialogue you can then:

- copy the launcher path
- install the desktop entry into your applications menu
- create a desktop shortcut

Some Linux desktop environments may still require you to use `Allow Launching` on the desktop shortcut before it behaves like a normal application launcher.

## Wrapper Scripts As A Convenience Option

The repository also still includes these launcher scripts:

- `ctk_theme_builder.sh`
- `ctk_theme_builder.bat`

These are convenience launchers for running CTk Theme Builder directly from a source checkout. They are useful if you:

- keep a local working copy of the project
- want a desktop shortcut that activates the local virtual environment for you
- do not want to activate the virtual environment manually before each run

They are not the primary packaged install path, and they are not installed automatically by `pip`.

In summary:

- installed package: prefer the environment's `ctk-theme-builder` command
- installed package with convenience launching: use `Tools -> Generate Launcher`
- source checkout: the repo-local wrapper scripts can be a practical option
