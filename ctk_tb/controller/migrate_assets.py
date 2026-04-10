"""Migrate user themes and palettes from a legacy install into the current user-data area."""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from pathlib import Path

USER_DATA_HOME = Path.home() / "CTkThemeBuilder"
THEMES_DIR = USER_DATA_HOME / "themes"
PALETTES_DIR = USER_DATA_HOME / "palettes"
STATE_DIR = USER_DATA_HOME / "state"
DB_FILE_PATH = STATE_DIR / "ctk_theme_builder.db"


def preference_value(db_file_path: Path, scope: str, preference_name: str) -> str | None:
    if not db_file_path.exists():
        return None

    db_conn = sqlite3.connect(db_file_path)
    try:
        cur = db_conn.cursor()
        cur.execute(
            """
            select preference_value
            from preferences
            where scope = :scope and preference_name = :preference_name
            """,
            {"scope": scope, "preference_name": preference_name},
        )
        row = cur.fetchone()
    finally:
        db_conn.close()

    if row is None:
        return None
    return row[0]


def legacy_paths(legacy_install_root: Path) -> tuple[Path, Path, Path]:
    legacy_db = legacy_install_root / "assets" / "data" / "ctk_theme_builder.db"
    legacy_palettes_dir = legacy_install_root / "assets" / "palettes"
    legacy_theme_dir_pref = preference_value(
        db_file_path=legacy_db,
        scope="user_preference",
        preference_name="theme_json_dir",
    )

    if legacy_theme_dir_pref is None:
        raise FileNotFoundError(
            f'Unable to determine legacy theme location from "{legacy_db}". '
            'Missing preference: user_preference/theme_json_dir.'
        )

    legacy_themes_dir = Path(legacy_theme_dir_pref).expanduser()
    if not legacy_themes_dir.is_absolute():
        legacy_themes_dir = (legacy_install_root / legacy_themes_dir).resolve()

    return legacy_db, legacy_themes_dir, legacy_palettes_dir


def target_theme_dir() -> Path:
    current_theme_dir_pref = preference_value(
        db_file_path=DB_FILE_PATH,
        scope="user_preference",
        preference_name="theme_json_dir",
    )
    if current_theme_dir_pref:
        return Path(current_theme_dir_pref).expanduser()
    return THEMES_DIR


def copy_if_missing(source_file: Path, target_file: Path) -> bool:
    if target_file.exists():
        return False
    target_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_file, target_file)
    return True


def copy_with_overwrite(source_file: Path, target_file: Path) -> None:
    target_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_file, target_file)


def migrate_assets(legacy_install_root: Path) -> int:
    legacy_install_root = legacy_install_root.expanduser().resolve()

    if not legacy_install_root.exists():
        print(f'ERROR: Legacy install location does not exist: {legacy_install_root}')
        return 1

    try:
        legacy_db, legacy_themes_dir, legacy_palettes_dir = legacy_paths(legacy_install_root)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        return 1

    if not legacy_db.exists():
        print(f'ERROR: Legacy preferences database not found: {legacy_db}')
        return 1

    if not legacy_themes_dir.exists():
        print(f'ERROR: Legacy theme directory not found: {legacy_themes_dir}')
        return 1

    target_themes_dir = target_theme_dir()
    target_palettes_dir = PALETTES_DIR
    target_themes_dir.mkdir(parents=True, exist_ok=True)
    target_palettes_dir.mkdir(parents=True, exist_ok=True)

    copied_themes = 0
    skipped_themes = 0
    copied_palettes = 0
    skipped_palettes = 0
    missing_palettes = 0

    print(f"Legacy install root : {legacy_install_root}")
    print(f"Legacy database     : {legacy_db}")
    print(f"Legacy themes       : {legacy_themes_dir}")
    print(f"Legacy palettes     : {legacy_palettes_dir}")
    print(f"Target themes       : {target_themes_dir}")
    print(f"Target palettes     : {target_palettes_dir}")
    print()

    for source_theme in sorted(legacy_themes_dir.glob("*.json"), key=lambda path: path.name.lower()):
        target_theme = target_themes_dir / source_theme.name
        theme_copied = copy_if_missing(source_theme, target_theme)
        if theme_copied:
            copied_themes += 1
            print(f"COPIED theme  : {source_theme.name}")
        else:
            skipped_themes += 1
            print(f"SKIPPED theme : {source_theme.name} already exists")

        source_palette = legacy_palettes_dir / source_theme.name
        target_palette = target_palettes_dir / source_theme.name
        if source_palette.exists():
            if theme_copied:
                copy_with_overwrite(source_palette, target_palette)
                copied_palettes += 1
            else:
                if copy_if_missing(source_palette, target_palette):
                    copied_palettes += 1
                else:
                    skipped_palettes += 1
        else:
            missing_palettes += 1
            print(f"WARNING: Missing source palette for {source_theme.name}")

    print()
    print(
        "Summary: "
        f"themes copied={copied_themes}, "
        f"themes skipped={skipped_themes}, "
        f"palettes copied={copied_palettes}, "
        f"palettes skipped={skipped_palettes}, "
        f"palettes missing={missing_palettes}"
    )

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Migrate themes and matching palettes from a legacy CTk Theme Builder install."
    )
    parser.add_argument(
        "legacy_install_root",
        help="Path to the old CTk Theme Builder install location.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return migrate_assets(Path(args.legacy_install_root))


if __name__ == "__main__":
    sys.exit(main())
