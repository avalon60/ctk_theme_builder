"""Generate platform-specific upgrade scripts for CTk Theme Builder."""

# Author: Clive Bostock
# Date: 2026-04-14
# Description: Creates upgrade scripts tied to the current Python environment.

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
import platform
import re
import shlex
import sys
from pathlib import Path

import ctk_tb.paths as app_paths

LINUX_UPGRADE_FILENAME = "upgrade-ctk-theme-builder.sh"
MACOS_UPGRADE_FILENAME = "upgrade-ctk-theme-builder.command"
WINDOWS_UPGRADE_FILENAME = "upgrade-ctk-theme-builder.bat"


class UpgradeScriptGenerationError(RuntimeError):
    """Raised when upgrade script generation fails."""


@dataclass(frozen=True)
class UpgradeScriptBundle:
    """Represents the generated upgrade script for the current platform."""

    system_name: str
    python_executable: Path
    script_path: Path
    generated_at: str
    app_version: str


def _preferred_python_executable(package_dir: Path, fallback: str | None = None) -> Path:
    """Return the owning virtualenv interpreter when the package is installed from one.

    When CTk Theme Builder is launched via a generated launcher, ``sys.executable``
    may point at a base interpreter with ``PYTHONPATH`` redirected into a virtual
    environment. In that case we prefer the virtualenv interpreter derived from the
    installed package location so upgrade scripts target the same environment that
    provided the package files.
    """
    site_packages_dir = package_dir.resolve().parent
    if site_packages_dir.name != "site-packages":
        return Path(fallback or sys.executable).expanduser()

    python_lib_dir = site_packages_dir.parent
    if python_lib_dir.name.startswith("python"):
        venv_root = python_lib_dir.parent.parent
    else:
        venv_root = python_lib_dir.parent
    executable_name = Path(fallback or sys.executable).name
    candidates = [
        venv_root / "bin" / executable_name,
        venv_root / "bin" / "python3",
        venv_root / "bin" / "python",
        venv_root / "Scripts" / "python.exe",
        venv_root / "Scripts" / "python",
    ]
    for candidate in candidates:
        if candidate.exists() and os.access(candidate, os.X_OK):
            return candidate

    return Path(fallback or sys.executable).expanduser()


def _application_version() -> str:
    """Return the current CTk Theme Builder application version."""
    model_file = app_paths.PACKAGE_DIR / "model" / "ctk_theme_builder.py"
    if not model_file.exists():
        return "0.0.0"

    content = model_file.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
    if match:
        return match.group(1)
    return "0.0.0"


def _generation_timestamp() -> str:
    """Return the upgrade-script generation timestamp."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _validate_python_path(python_executable: Path) -> None:
    """Validate the requested Python interpreter path."""
    if not python_executable.exists() or not os.access(python_executable, os.X_OK):
        raise UpgradeScriptGenerationError(
            f"Python interpreter path is invalid or not executable: {python_executable}"
        )


def _set_executable(path: Path) -> None:
    """Ensure a file is executable."""
    try:
        current_mode = path.stat().st_mode
        path.chmod(current_mode | 0o755)
    except PermissionError as exc:
        raise UpgradeScriptGenerationError(
            f"Unable to update permissions for {path}: {exc}"
        ) from exc


def _write_text_file(path: Path, content: str) -> None:
    """Write a text file with UTF-8 encoding."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise UpgradeScriptGenerationError(f"Unable to write upgrade script {path}: {exc}") from exc


def _linux_upgrade_text(python_executable: Path, generated_at: str) -> str:
    quoted_python = shlex.quote(str(python_executable))
    app_version = _application_version()
    return (
        "#!/usr/bin/env bash\n"
        "# Author: Clive Bostock\n"
        f"# Date: {generated_at.split()[0]}\n"
        "# Description: Upgrade CTk Theme Builder in its associated virtual environment.\n\n"
        f"# Python: {python_executable}\n"
        f"# Version: {app_version}\n\n"
        "set -euo pipefail\n\n"
        "VENV_PYTHON="
        f"{quoted_python}\n\n"
        '"${VENV_PYTHON}" -m pip install --upgrade ctk-theme-builder\n'
    )


def _windows_upgrade_text(python_executable: Path, generated_at: str) -> str:
    app_version = _application_version()
    return (
        "@echo off\n"
        "REM Author: Clive Bostock\n"
        f"REM Date: {generated_at.split()[0]}\n"
        "REM Description: Upgrade CTk Theme Builder in its associated virtual environment.\n\n"
        f"REM Python: {python_executable}\n"
        f"REM Version: {app_version}\n\n"
        f"set \"VENV_PYTHON={python_executable}\"\n\n"
        "\"%VENV_PYTHON%\" -m pip install --upgrade ctk-theme-builder\n"
        "if errorlevel 1 exit /b %errorlevel%\n"
    )


def generate_upgrade_script(
        target_dir: Path | None = None,
        python_executable: str | None = None,
        system_name: str | None = None) -> UpgradeScriptBundle:
    """Generate the upgrade script for the current or specified platform."""
    target_dir = target_dir or app_paths.UPGRADES_DIR
    system_name = system_name or platform.system()
    python_path = _preferred_python_executable(app_paths.PACKAGE_DIR, python_executable)
    generated_at = _generation_timestamp()
    app_version = _application_version()

    _validate_python_path(python_path)

    if system_name == "Windows":
        script_path = target_dir / WINDOWS_UPGRADE_FILENAME
        _write_text_file(script_path, _windows_upgrade_text(python_path, generated_at))
    elif system_name == "Darwin":
        script_path = target_dir / MACOS_UPGRADE_FILENAME
        _write_text_file(script_path, _linux_upgrade_text(python_path, generated_at))
        _set_executable(script_path)
    else:
        script_path = target_dir / LINUX_UPGRADE_FILENAME
        _write_text_file(script_path, _linux_upgrade_text(python_path, generated_at))
        _set_executable(script_path)

    return UpgradeScriptBundle(
        system_name=system_name,
        python_executable=python_path,
        script_path=script_path,
        generated_at=generated_at,
        app_version=app_version,
    )
