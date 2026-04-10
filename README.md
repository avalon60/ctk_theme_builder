# CTk Theme Builder

CTk Theme Builder is a desktop editor for creating, previewing, and refining themes for [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) applications.

It provides a live preview workflow for adjusting colours, geometry, palettes, and theme metadata without editing theme JSON files by hand.

## Features

- Visual theme editing with live preview
- Support for light and dark theme variants
- Theme geometry editing for supported widget properties
- Palette management and colour harmonics tools
- Theme merge and import/export support
- Provenance tracking for theme metadata
- Built-in theme and palette assets to get started quickly

## Installation

Install from PyPI:

```bash
pip install ctk-theme-builder
```

## Usage

Launch the application:

```bash
ctk-theme-builder
```

Optional command-line arguments:

```bash
ctk-theme-builder --set-appearance Dark
ctk-theme-builder --set-theme /path/to/theme.json
```

To migrate themes and palettes from a legacy installation:

```bash
ctktb-migrate-assets /path/to/old/install
```

## Requirements

- Python 3.10 to 3.13
- A desktop environment capable of running Tk-based GUI applications

## Documentation

- Installation and upgrade notes: [docs/installs-upgrades.md](docs/installs-upgrades.md)
- User guides and release notes: [project wiki](https://github.com/avalon60/ctk_theme_builder/wiki)
- Source code and issue tracker: [GitHub repository](https://github.com/avalon60/ctk_theme_builder)

## Licence

Released under the MIT Licence. See [LICENSE](LICENSE).
