"""Helpers for best-effort CTk Theme Builder update checks."""

# Author: Clive Bostock
# Date: 2026-04-21
# Description: Queries PyPI for the latest CTk Theme Builder version with a short timeout.

from __future__ import annotations

import json
import urllib.error
import urllib.request

from packaging.version import InvalidVersion
from packaging.version import Version

import ctk_tb.utils.loggerutl as log

PYPI_PROJECT_JSON_URL = 'https://pypi.org/pypi/ctk-theme-builder/json'
PYPI_TIMEOUT_S = 2.5
_UPDATE_CHECK_CACHE: tuple[bool, str] | None = None


def fetch_update_status(current_version: str, timeout_s: float = PYPI_TIMEOUT_S) -> tuple[bool, str] | None:
    """Return update availability and latest version from PyPI when reachable.

    Args:
        current_version: The version currently running in the application.
        timeout_s: Timeout for the PyPI request in seconds.

    Returns:
        A tuple of ``(update_available, latest_version)`` when the lookup
        succeeds, otherwise ``None``.
    """
    global _UPDATE_CHECK_CACHE

    if _UPDATE_CHECK_CACHE is not None:
        return _UPDATE_CHECK_CACHE

    try:
        with urllib.request.urlopen(PYPI_PROJECT_JSON_URL, timeout=timeout_s) as response:
            payload = json.load(response)
        latest_version = payload['info']['version']
        update_available = Version(latest_version) > Version(current_version)
    except (OSError, ValueError, KeyError, InvalidVersion, urllib.error.URLError) as error:
        log.log_debug(
            log_text=f'Update check unavailable: {error}',
            class_name='update_check',
            method_name='fetch_update_status',
        )
        return None

    _UPDATE_CHECK_CACHE = (update_available, latest_version)
    return _UPDATE_CHECK_CACHE
