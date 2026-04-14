"""Explicit runtime initialisation for CTk Theme Builder."""

# Author: Clive Bostock
# Date: 2026-04-12
# Description: Handles startup directory, database, migration, and update initialisation.

from __future__ import annotations

import getpass
import json
import re
import shutil
import sqlite3
from pathlib import Path

import ctk_tb.paths as app_paths

CURRENT_RUNTIME_LAYOUT_VERSION = "1"
RUNTIME_LAYOUT_MARKER = app_paths.STATE_DIR / "runtime_layout_version.json"

_BOOTSTRAPPED = False


def current_app_version() -> str:
    """Return the application version embedded in the model module."""
    model_file = app_paths.PACKAGE_DIR / "model" / "ctk_theme_builder.py"
    if not model_file.exists():
        return "0.0.0"
    content = model_file.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
    if match:
        return match.group(1)
    return "0.0.0"


def version_scalar(version: str) -> int:
    """Convert dotted application version text into a sortable integer."""
    parts = version.split(".")
    while len(parts) < 3:
        parts.append("0")
    padded = [int(part) for part in parts[:3]]
    return padded[0] * 1_000_000 + padded[1] * 1_000 + padded[2]


def create_database(db_file_path: Path) -> None:
    """Create the runtime SQLite database if it does not yet exist."""
    db_conn = sqlite3.connect(db_file_path)
    cur = db_conn.cursor()

    cur.execute(
        """create table if not exists
        preferences (
          scope            text not null,
          preference_name  text not null,
          preference_value text not null,
          data_type        text not null,
          preference_attr1 text,
          preference_attr2 text,
          preference_attr3 text,
          primary key (scope, preference_name)
      )"""
    )

    cur.execute(
        """create table if not exists
        application_control (
          record_number        integer primary key,
          app_version          text,
          previous_app_version text
      )"""
    )
    cur.execute(
        "insert or ignore into application_control (record_number, app_version, previous_app_version) "
        "values (1, '1.9.9', '1.9.9')"
    )

    cur.execute(
        """create table if not exists
        colour_palette_entries (
            entry_id int primary key,
            row      int,
            col      int,
            label    text
        )"""
    )

    cur.execute(
        """create table if not exists
        colour_cascade_properties (
            entry_id        int,
            widget_type     text,
            widget_property text,
            primary key (entry_id, widget_type, widget_property)
        )"""
    )

    db_conn.commit()
    db_conn.close()


def app_versions(db_file_path: Path) -> tuple[str, str]:
    """Return the current and previous recorded application versions."""
    db_conn = sqlite3.connect(db_file_path)
    cur = db_conn.cursor()
    cur.execute("select app_version, previous_app_version from application_control where record_number = 1")
    record = cur.fetchone()
    db_conn.close()
    if record is None:
        return "2.0.0", "0.0.0"
    return record[0], record[1]


def update_app_version(db_file_path: Path, new_app_version: str) -> None:
    """Update the stored application version in the runtime database."""
    current_version, _ = app_versions(db_file_path)
    if current_version == new_app_version:
        return
    db_conn = sqlite3.connect(db_file_path)
    cur = db_conn.cursor()
    cur.execute(
        "update application_control set previous_app_version = app_version where record_number = 1"
    )
    cur.execute(
        "update application_control set app_version = :app_version where record_number = 1",
        {"app_version": new_app_version},
    )
    db_conn.commit()
    db_conn.close()


def copy_missing_files(source_dir: Path, target_dir: Path, skip_names: set[str] | None = None) -> None:
    """Copy files from a source directory into a target directory without overwriting."""
    if not source_dir.exists():
        return
    target_dir.mkdir(parents=True, exist_ok=True)
    skip_names = skip_names or set()
    for source_file in source_dir.iterdir():
        if not source_file.is_file():
            continue
        if source_file.name in skip_names:
            continue
        target_file = target_dir / source_file.name
        if not target_file.exists():
            shutil.copy2(source_file, target_file)


def initialise_user_dirs() -> None:
    """Create the runtime directory structure if it is missing."""
    for directory in (
        app_paths.USER_DATA_HOME,
        app_paths.THEMES_DIR,
        app_paths.PALETTES_DIR,
        app_paths.STATE_DIR,
        app_paths.TMP_DIR,
        app_paths.LOG_DIR,
        app_paths.LAUNCHERS_DIR,
        app_paths.UPGRADES_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)


def ensure_database() -> None:
    """Ensure the runtime database exists, copying forward the legacy copy if present."""
    legacy_db = app_paths.ASSETS_DIR / "data" / "ctk_theme_builder.db"
    if app_paths.DB_FILE_PATH.exists():
        return
    if legacy_db.exists():
        shutil.copy2(legacy_db, app_paths.DB_FILE_PATH)
    else:
        create_database(app_paths.DB_FILE_PATH)


def migrate_legacy_user_files() -> None:
    """Seed runtime themes and palettes from bundled sources when needed."""
    deleted_names = app_paths.deleted_seed_themes()
    copy_missing_files(app_paths.INSTALL_ROOT / "user_themes", app_paths.THEMES_DIR, skip_names=deleted_names)
    copy_missing_files(app_paths.ASSETS_DIR / "palettes", app_paths.PALETTES_DIR, skip_names=deleted_names)

    if not any(app_paths.THEMES_DIR.glob("*.json")):
        copy_missing_files(app_paths.APP_THEMES_DIR, app_paths.THEMES_DIR)


def apply_repo_updates(db_file_path: Path) -> None:
    """Apply version-gated SQL updates defined in the bundled repo update manifest."""
    updates_json_file = app_paths.CONFIG_DIR / "repo_updates.json"
    if not updates_json_file.exists():
        return

    with updates_json_file.open(encoding="utf-8") as json_file:
        updates_dict = json.load(json_file)

    registered_app_version, _ = app_versions(db_file_path)
    target_app_version = current_app_version()
    os_user_name = getpass.getuser()

    db_conn = sqlite3.connect(db_file_path)
    try:
        cur = db_conn.cursor()

        for sql_id in updates_dict:
            sql_apply_version = updates_dict[sql_id]["sql_apply_version"]
            if not (
                version_scalar(registered_app_version)
                < version_scalar(sql_apply_version)
                <= version_scalar(target_app_version)
            ):
                continue

            sql_statement = updates_dict[sql_id]["sql_statement"]
            sql_statement = sql_statement.replace("%os_user_name%", os_user_name)
            sql_statement = sql_statement.replace("%user_themes_location%", str(app_paths.THEMES_DIR))
            cur.execute(sql_statement)

        db_conn.commit()
    except sqlite3.OperationalError:
        return
    finally:
        db_conn.close()

    try:
        update_app_version(db_file_path, target_app_version)
    except sqlite3.OperationalError:
        return


def ensure_theme_dir_preference(db_file_path: Path) -> None:
    """Ensure the runtime theme directory preference points at the runtime theme folder."""
    db_conn = sqlite3.connect(db_file_path)
    try:
        cur = db_conn.cursor()
        cur.execute(
            """
            insert into preferences (scope, preference_name, preference_value, data_type)
            values ('user_preference', 'theme_json_dir', :preference_value, 'Path')
            on conflict(scope, preference_name)
            do update set preference_value = excluded.preference_value, data_type = excluded.data_type
            """,
            {"preference_value": str(app_paths.THEMES_DIR)},
        )
        db_conn.commit()
    except sqlite3.OperationalError:
        return
    finally:
        db_conn.close()


def read_runtime_layout_version() -> str | None:
    """Return the recorded runtime layout version, if present."""
    if not RUNTIME_LAYOUT_MARKER.exists():
        return None
    try:
        marker_content = json.loads(RUNTIME_LAYOUT_MARKER.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(marker_content, dict):
        return None
    version = marker_content.get("runtime_layout_version")
    if isinstance(version, str):
        return version
    return None


def write_runtime_layout_version(version: str = CURRENT_RUNTIME_LAYOUT_VERSION) -> None:
    """Persist the current runtime layout version marker."""
    RUNTIME_LAYOUT_MARKER.write_text(
        json.dumps({"runtime_layout_version": version}, indent=2),
        encoding="utf-8",
    )


def initialise_runtime_state() -> None:
    """Initialise the runtime environment at an explicit startup boundary."""
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return

    initialise_user_dirs()
    ensure_database()

    current_layout_version = read_runtime_layout_version()
    if current_layout_version != CURRENT_RUNTIME_LAYOUT_VERSION:
        migrate_legacy_user_files()
        write_runtime_layout_version()

    apply_repo_updates(app_paths.DB_FILE_PATH)
    ensure_theme_dir_preference(app_paths.DB_FILE_PATH)
    _BOOTSTRAPPED = True
