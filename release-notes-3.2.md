# CTk Theme Builder 3.2.x

This release focuses on packaging readiness, developer workflow improvements, and a round of UI and theme refinements.

## What's new

- Added Poetry-based packaging and release preparation.
- Improved PyPI readiness with updated project metadata, README polish, and more reliable test bootstrapping.
- Added an icon browser.
- Added a runtime log viewer.
- Improved preview-panel startup and handshake reliability.
- Refined asset migration behaviour during upgrades/startup.
- Added the new `Phoenix` theme.
- Applied colour refinements to:
  - `Anthracite`
  - `Cobalt`
  - `DaynNight`
  - `GhostTrain`
  - `Greengage`
  - `GreyGhost`
  - `Hades`
  - `Harlequin`
  - `TrojanBlue`

## Developer and release tooling

- Added/updated release helper scripts, including wheel install testing and publishing support.
- Modernised launcher, interpreter, and virtual-environment handling.
- Updated installation, upgrade, and user documentation.
- Added or refreshed tests around preferences and utility behaviour.

## Notes

- This release continues the move towards a cleaner `ctk_tb` package structure.
- The main emphasis has been on making the application easier to package, test, release, and maintain.
