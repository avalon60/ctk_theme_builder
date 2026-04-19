# CTk Theme Builder

![CTk Theme Builder](assets/images/ctk-tb-logo.png)

CTk Theme Builder is a desktop editor for creating, previewing, and refining themes for [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) applications.

It provides a live, visual workflow for editing CustomTkinter theme colours, supported widget geometry, palettes, and theme metadata without hand-editing theme JSON files.

The application is designed to make iterative theme work practical: you can experiment with colours, compare light and dark appearance modes, reuse palette colours across a theme, and validate the result against realistic widget rendering as you work.

## Features

- Live visual editing of CustomTkinter theme colours with immediate preview feedback
- Editing of supported widget geometry properties such as corner radius and border width
- Light and dark appearance-mode workflows, including copying and flipping values between modes
- Persistent theme palette for planning, reusing, and refining colours across a theme
- Colour harmonics generation from a keystone colour to help build coherent palettes
- Bundled icon browsing with CustomTkinter code-snippet generation for available Font Awesome icons
- Drag-and-drop, clipboard, and shade-adjustment workflows for fast colour iteration
- Palette-driven cascade updates for applying a colour across related widget properties
- Theme merge, import, and export support for reuse and distribution
- Provenance metadata for themes created and maintained in the builder
- Preview and validation support for realistic widget states, including disabled rendering
- Built-in theme and palette assets to help you get started quickly

## Installation

Recommended installation from PyPI, using a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install ctk-theme-builder
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install ctk-theme-builder
```

Alternative install methods for users who already use `uv`:

```bash
uv pip install ctk-theme-builder
uvx --from ctk-theme-builder ctk-theme-builder
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
- User guide: [docs/UserGuide-3.3.md](docs/UserGuide-3.3.md)
- Release notes: [release-notes-3.2.4.md](release-notes-3.2.4.md)

## Licence

Released under the MIT Licence. See [LICENSE](LICENSE).
