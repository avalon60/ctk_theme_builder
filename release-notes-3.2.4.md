# CTk Theme Builder 3.2.4

This patch release focuses on startup reliability, launch convenience, compatibility cleanup, and documentation polish.

## What's new

- Added `Tools -> Generate Launcher` to create a platform-specific convenience launcher under `~/CTkThemeBuilder/launchers`
- Added a launcher result dialogue with a `Copy Path` button and clipboard icon
- Hardened preview startup so slower preview initialisation does not trigger false listener timeout failures as easily
- Improved preview listener startup failure handling when the configured port is already in use, with clearer guidance to close the other instance or change the listener port in Preferences
- Added Python interpreter version to the About dialogue

## Compatibility and runtime changes

- Moved runtime initialisation to an explicit startup boundary instead of import-time bootstrap
- Added a runtime-layout marker for clearer bootstrap and migration handling
- Removed `text_color_disabled` from theme JSON, theme views, and migration output in preparation for newer CustomTkinter behaviour
- Added an in-memory compatibility shim so current CustomTkinter releases that still expect `text_color_disabled` continue to work
- Improved logging/bootstrap safety so imports are less brittle before runtime initialisation completes

## Documentation

- Updated the README installation section to recommend virtual-environment usage explicitly
- Added `uv` install/run alternatives to the README for users who already use `uv`
- Reworked `docs/installs-upgrades.md` into a cleaner install, upgrade, and migration note
- Added guidance on wrapper scripts as convenience launchers for source-checkout use
