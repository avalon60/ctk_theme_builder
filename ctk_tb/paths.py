"""Runtime path and bootstrap helpers for CTk Theme Builder."""

from __future__ import annotations

import getpass
import json
import re
import shutil
import sqlite3
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
DB_FILE_PATH = STATE_DIR / "ctk_theme_builder.db"

QA_STOP_FILE = TMP_DIR / "qa_application.stop"
QA_STARTED_FILE = TMP_DIR / "qa_application.started"
LISTENER_FILE = TMP_DIR / "listener.started"

_BOOTSTRAPPED = False


def current_app_version() -> str:
    model_file = PACKAGE_DIR / "model" / "ctk_theme_builder.py"
    if not model_file.exists():
        return "0.0.0"
    content = model_file.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
    if match:
        return match.group(1)
    return "0.0.0"


def version_scalar(version: str) -> int:
    parts = version.split(".")
    while len(parts) < 3:
        parts.append("0")
    padded = [int(part) for part in parts[:3]]
    return padded[0] * 1_000_000 + padded[1] * 1_000 + padded[2]


def create_database(db_file_path: Path) -> None:
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
    db_conn = sqlite3.connect(db_file_path)
    cur = db_conn.cursor()
    cur.execute("select app_version, previous_app_version from application_control where record_number = 1")
    record = cur.fetchone()
    db_conn.close()
    if record is None:
        return "2.0.0", "0.0.0"
    return record[0], record[1]


def update_app_version(db_file_path: Path, new_app_version: str) -> None:
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


def copy_missing_files(source_dir: Path, target_dir: Path) -> None:
    if not source_dir.exists():
        return
    target_dir.mkdir(parents=True, exist_ok=True)
    for source_file in source_dir.iterdir():
        if not source_file.is_file():
            continue
        target_file = target_dir / source_file.name
        if not target_file.exists():
            shutil.copy2(source_file, target_file)


def migrate_legacy_user_files() -> None:
    copy_missing_files(INSTALL_ROOT / "user_themes", THEMES_DIR)
    copy_missing_files(ASSETS_DIR / "palettes", PALETTES_DIR)

    # If no user themes were shipped separately, seed from the bundled built-in themes.
    if not any(THEMES_DIR.glob("*.json")):
        copy_missing_files(APP_THEMES_DIR, THEMES_DIR)


def initialise_user_dirs() -> None:
    for directory in (USER_DATA_HOME, THEMES_DIR, PALETTES_DIR, STATE_DIR, TMP_DIR, LOG_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def ensure_database() -> None:
    legacy_db = ASSETS_DIR / "data" / "ctk_theme_builder.db"
    if DB_FILE_PATH.exists():
        return
    if legacy_db.exists():
        shutil.copy2(legacy_db, DB_FILE_PATH)
    else:
        create_database(DB_FILE_PATH)


def apply_repo_updates(db_file_path: Path) -> None:
    updates_json_file = CONFIG_DIR / "repo_updates.json"
    if not updates_json_file.exists():
        return

    with updates_json_file.open(encoding="utf-8") as json_file:
        updates_dict = json.load(json_file)

    registered_app_version, _ = app_versions(db_file_path)
    target_app_version = current_app_version()
    os_user_name = getpass.getuser()

    db_conn = sqlite3.connect(db_file_path)
    cur = db_conn.cursor()

    for sql_id in updates_dict:
        sql_apply_version = updates_dict[sql_id]["sql_apply_version"]
        if not (version_scalar(registered_app_version) < version_scalar(sql_apply_version) <= version_scalar(target_app_version)):
            continue

        sql_statement = updates_dict[sql_id]["sql_statement"]
        sql_statement = sql_statement.replace("%os_user_name%", os_user_name)
        sql_statement = sql_statement.replace("%user_themes_location%", str(THEMES_DIR))
        cur.execute(sql_statement)

    db_conn.commit()
    db_conn.close()
    update_app_version(db_file_path, target_app_version)


def ensure_theme_dir_preference(db_file_path: Path) -> None:
    db_conn = sqlite3.connect(db_file_path)
    cur = db_conn.cursor()
    cur.execute(
        """
        insert into preferences (scope, preference_name, preference_value, data_type)
        values ('user_preference', 'theme_json_dir', :preference_value, 'Path')
        on conflict(scope, preference_name)
        do update set preference_value = excluded.preference_value, data_type = excluded.data_type
        """,
        {"preference_value": str(THEMES_DIR)},
    )
    db_conn.commit()
    db_conn.close()


def bootstrap_user_data() -> None:
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return
    initialise_user_dirs()
    ensure_database()
    migrate_legacy_user_files()
    apply_repo_updates(DB_FILE_PATH)
    ensure_theme_dir_preference(DB_FILE_PATH)
    _BOOTSTRAPPED = True


bootstrap_user_data()
