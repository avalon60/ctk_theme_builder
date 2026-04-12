"""Compatibility helpers for theme dictionaries."""

# Author: Clive Bostock
# Date: 2026-04-12
# Description: Applies in-memory theme compatibility shims for differing CustomTkinter versions.

from __future__ import annotations

from customtkinter import ThemeManager


def backfill_text_color_disabled(theme: dict | None = None) -> None:
    """Backfill missing ``text_color_disabled`` entries in the active theme.

    CTk Theme Builder is removing ``text_color_disabled`` from its JSON theme
    files ahead of CustomTkinter 5.3. Some installed CustomTkinter versions
    still expect that key in ``ThemeManager.theme`` for a subset of widgets.
    This helper keeps the on-disk JSON clean while restoring an in-memory
    compatibility value for older runtimes.
    """
    if theme is None:
        theme = ThemeManager.theme

    if not isinstance(theme, dict):
        return

    for widget_name, widget_data in theme.items():
        if not isinstance(widget_data, dict):
            continue
        if "text_color_disabled" in widget_data:
            continue
        text_color = widget_data.get("text_color")
        if text_color is not None:
            widget_data["text_color_disabled"] = text_color
