"""Runtime path helpers for CTk Theme Builder."""

# Author: Clive Bostock
# Date: 2026-04-12
# Description: Defines package and runtime paths plus lightweight state helpers.

from __future__ import annotations

import json
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
INSTALL_ROOT = PACKAGE_DIR.parent

ASSETS_DIR = INSTALL_ROOT / "assets"
LIB_DIR = INSTALL_ROOT / "lib"
CONFIG_DIR = ASSETS_DIR / "config"
ETC_DIR = ASSETS_DIR / "etc"
VIEWS_DIR = ASSETS_DIR / "views"
APP_THEMES_DIR = ASSETS_DIR / "themes"
APP_IMAGES = ASSETS_DIR / "images"

USER_DATA_HOME = Path.home() / "CTkThemeBuilder"
THEMES_DIR = USER_DATA_HOME / "themes"
PALETTES_DIR = USER_DATA_HOME / "palettes"
STATE_DIR = USER_DATA_HOME / "state"
TMP_DIR = USER_DATA_HOME / "tmp"
LOG_DIR = USER_DATA_HOME / "logs"
LAUNCHERS_DIR = USER_DATA_HOME / "launchers"
UPGRADES_DIR = USER_DATA_HOME / "upgrades"
DB_FILE_PATH = STATE_DIR / "ctk_theme_builder.db"

QA_STOP_FILE = TMP_DIR / "qa_application.stop"
QA_STARTED_FILE = TMP_DIR / "qa_application.started"
LISTENER_FILE = TMP_DIR / "listener.started"
DELETED_SEED_THEMES_FILE = STATE_DIR / "deleted_seed_themes.json"


def deleted_seed_themes() -> set[str]:
    """Return the set of seeded theme names the user has explicitly deleted."""
    if not DELETED_SEED_THEMES_FILE.exists():
        return set()

    try:
        deleted_names = json.loads(DELETED_SEED_THEMES_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()

    if not isinstance(deleted_names, list):
        return set()
    return {name for name in deleted_names if isinstance(name, str)}


def save_deleted_seed_themes(theme_names: set[str]) -> None:
    """Persist the set of seeded theme names suppressed from future reseeding."""
    DELETED_SEED_THEMES_FILE.write_text(
        json.dumps(sorted(theme_names), indent=2),
        encoding="utf-8",
    )


def mark_seed_theme_deleted(theme_name: str) -> None:
    """Record that a previously seeded theme has been deliberately deleted."""
    deleted_names = deleted_seed_themes()
    deleted_names.add(theme_name)
    save_deleted_seed_themes(deleted_names)
