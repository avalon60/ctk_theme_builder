# CTk Theme Builder 3.2 Series

This document summarises the changes discovered in git for the tagged `3.2.x` release series.
Each section is based on the commits introduced up to the named tag.

## `v3.2.1`

- Moved the project into a Poetry-managed, wheel-oriented packaging flow.
- Introduced the `ctk_tb` package structure, `pyproject.toml`, `poetry.lock`, and new packaging/release scripts.
- Added runtime bootstrap work, including `ctk_tb.runtime_init`, `ctk_tb.paths`, and cleaner startup boundaries.
- Added the runtime log viewer and the icon browser.
- Improved preview startup and handshake behaviour.
- Added asset-migration support for older installs.
- Refreshed install and release documentation, including the release artefact guide.
- Added the `Phoenix` theme and a broad round of palette/theme refinements.
- Added tests around preferences and utility behaviour.

## `v3.2.2`

- Added Python interpreter version reporting to the About dialogue.

## `v3.2.3`

- Expanded the README installation guidance.

## `v3.2.8`

- Added `Tools -> Generate Launcher`.
- Hardened preview startup and improved preview listener error handling.
- Added refreshed logo/icon assets, including the taskbar icon image.
- Updated the user guide and install/upgrade documentation for the launcher flow.
- Refreshed exported requirements and packaging support for the mid-series releases.

## `v3.2.9`

- Improved launcher generation across platforms.
- Added a Windows `.ico` asset and expanded generated icon/logo variants.
- Updated install/upgrade documentation to match the launcher improvements.

## `v3.2.10`

- Added `Tools -> Generate Upgrade Script`.
- Documented the Tools menu and fixed QA theme compatibility.
- Updated the user guide and removed older superseded user guides from `docs/`.

## `v3.2.11`

- Fixed icon-browser theme compatibility.
- Restored disabled button text colours in theme assets.
- Refined publish/release helper behaviour.

## `v3.2.12`

- Fixed generated launchers and upgrade scripts so they target the owning virtual environment more reliably.

## `v3.2.13`

- Added version metadata to generated upgrade scripts.
- Restored disabled text theme properties across the shipped themes and skeleton/default theme files.

## `v3.2.14`

- Updated the version-bump scripts so they output the new version cleanly.

## `v3.2.15`

- Exposed disabled text colours in the control panel and preview/runtime flow.
- Added repository/runtime update entries and updated shipped theme views to surface the new properties.

## Notes

- There are no `v3.2.4`, `v3.2.5`, `v3.2.6`, or `v3.2.7` tags in the repository.
- The `3.2.x` line is the release series where the project shifted decisively from legacy ZIP-style deployment towards wheel/PyPI packaging, launcher generation, upgrade scripting, and runtime migration support.
