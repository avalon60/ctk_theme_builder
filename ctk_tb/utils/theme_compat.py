"""Compatibility helpers for theme dictionaries."""

# Author: Clive Bostock
# Date: 2026-04-12
# Description: Applies in-memory theme compatibility shims for differing CustomTkinter versions.

from __future__ import annotations

from customtkinter import ThemeManager


def normalise_label_theme(theme: dict) -> None:
    """Add v6 label borders and omit the obsolete theme disabled-colour entry.

    Args:
        theme: Theme dictionary to normalise in memory without overwriting borders.
    """
    label = theme.get("CTkLabel")
    if not isinstance(label, dict):
        return
    label.setdefault("border_width", 0)
    label.setdefault("border_color", ["#979DA2", "#565B5E"])
    label.pop("text_color_disabled", None)


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

    normalise_label_theme(theme)

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
