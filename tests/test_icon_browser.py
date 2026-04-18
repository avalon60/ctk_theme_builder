"""Tests for the icon browser preview error handling."""

# Author: Clive Bostock
# Date: 2026-04-18
# Description: Verify concise preview error messages for icon browser failures.

from ctk_tb.view.ctk_fa_browser import _preview_error_message


def test_preview_error_message_for_missing_customtkinter():
    """Return a targeted message when CustomTkinter image support is missing."""
    error = RuntimeError(
        "icon_to_ctkimage() requires CustomTkinter. "
        "Install it with `pip install customtkinter`."
    )

    assert _preview_error_message(error) == (
        "Icon preview is unavailable because CustomTkinter image support "
        "is not installed."
    )


def test_preview_error_message_for_missing_pillow():
    """Return a targeted message when Pillow image support is missing."""
    error = RuntimeError("The default Pillow backend requires Pillow.")

    assert _preview_error_message(error) == (
        "Icon preview is unavailable because Pillow image support "
        "is not installed."
    )


def test_preview_error_message_for_other_errors_uses_first_line():
    """Keep unexpected preview errors concise and single-line."""
    error = ValueError("bad svg\nfull traceback detail")

    assert _preview_error_message(error) == "Icon preview unavailable: bad svg"
