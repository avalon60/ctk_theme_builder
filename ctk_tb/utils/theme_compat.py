"""Compatibility helpers for theme dictionaries."""

# Author: Clive Bostock
# Date: 2026-04-12
# Description: Applies in-memory theme compatibility shims for differing CustomTkinter versions.

from __future__ import annotations

import copy
import json

from customtkinter import ThemeManager

from ctk_tb.paths import ETC_DIR


def normalise_theme(theme: dict, scaffold: dict | None = None) -> None:
    """Fill missing theme properties from the scaffold without replacing values.

    Args:
        theme: Theme dictionary to update in memory.
        scaffold: Optional reference dictionary; defaults to the bundled scaffold.

    Raises:
        ValueError: A widget section is not a dictionary.
        OSError: The bundled scaffold cannot be read.
        json.JSONDecodeError: The bundled scaffold is malformed.
    """
    if scaffold is None:
        with (ETC_DIR / "theme_skeleton.json").open(encoding="utf-8") as source:
            scaffold = json.load(source)

    def fill_missing(target: dict, reference: dict, location: str) -> None:
        """Copy missing defaults recursively, keeping mutable values independent."""
        for key, value in reference.items():
            if key not in target:
                target[key] = copy.deepcopy(value)
            elif isinstance(value, dict):
                if not isinstance(target[key], dict):
                    raise ValueError(f"Theme section {location}{key} must be a dictionary")
                fill_missing(target[key], value, f"{location}{key}.")

    # Provenance describes the user's file and is not widget configuration.
    widget_defaults = {key: value for key, value in scaffold.items() if key != "provenance"}
    fill_missing(theme, widget_defaults, "")
    label = theme.get("CTkLabel")
    if isinstance(label, dict):
        label.pop("text_color_disabled", None)


def normalise_label_theme(theme: dict) -> None:
    """Normalise only label data using the scaffold's canonical defaults.

    Args:
        theme: Theme dictionary whose existing label section should be updated.
    """
    label = theme.get("CTkLabel")
    if not isinstance(label, dict):
        return
    with (ETC_DIR / "theme_skeleton.json").open(encoding="utf-8") as source:
        scaffold = json.load(source)
    normalise_theme(theme, {"CTkLabel": scaffold["CTkLabel"]})


def backfill_text_color_disabled(theme: dict | None = None) -> None:
    """Backfill missing ``text_color_disabled`` entries in the active theme.

    Labels follow the v6 theme schema and are excluded.

    Other widgets may still require this key when loading older themes.
    Restore their in-memory fallback without changing on-disk theme files.
    """
    if theme is None:
        theme = ThemeManager.theme

    if not isinstance(theme, dict):
        return

    for widget_name, widget_data in theme.items():
        if widget_name == "CTkLabel":
            continue
        if not isinstance(widget_data, dict):
            continue
        if "text_color_disabled" in widget_data:
            continue
        text_color = widget_data.get("text_color")
        if text_color is not None:
            widget_data["text_color_disabled"] = text_color

    normalise_theme(theme)
