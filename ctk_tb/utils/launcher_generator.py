"""Generate convenience launcher scripts for the current platform."""

# Author: Clive Bostock
# Date: 2026-04-12
# Description: Creates OS-specific launcher scripts using the current interpreter and controller path.

from __future__ import annotations

import os
import platform
import shlex
import sys
from pathlib import Path

import ctk_tb.paths as app_paths


def launcher_output_path(target_dir: Path | None = None, system_name: str | None = None) -> Path:
    """Return the launcher output path for the supplied or current platform."""
    if target_dir is None:
        target_dir = app_paths.LAUNCHERS_DIR

    system_name = system_name or platform.system()
    if system_name == "Windows":
        filename = "ctk-theme-builder.bat"
    elif system_name == "Darwin":
        filename = "ctk-theme-builder.command"
    else:
        filename = "ctk-theme-builder.sh"
    return target_dir / filename


def launcher_script_text(
        python_executable: str | None = None,
        controller_script: Path | None = None,
        system_name: str | None = None) -> str:
    """Return platform-appropriate launcher script content."""
    python_executable = python_executable or sys.executable
    controller_script = controller_script or (app_paths.PACKAGE_DIR / "controller" / "ctk_theme_builder.py")
    system_name = system_name or platform.system()

    if system_name == "Windows":
        return (
            "@echo off\n"
            ":: Author: Clive Bostock\n"
            ":: Date: 2026-04-12\n"
            ":: Description: CTk Theme Builder launcher generated for the current Python environment.\n"
            f"set \"PYTHON_EXE={python_executable}\"\n"
            f"set \"CTK_THEME_BUILDER={controller_script}\"\n"
            "\"%PYTHON_EXE%\" \"%CTK_THEME_BUILDER%\" %*\n"
        )

    quoted_python = shlex.quote(python_executable)
    quoted_controller = shlex.quote(str(controller_script))
    return (
        "#!/usr/bin/env bash\n"
        "# Author: Clive Bostock\n"
        "# Date: 2026-04-12\n"
        "# Description: CTk Theme Builder launcher generated for the current Python environment.\n"
        f"exec {quoted_python} {quoted_controller} \"$@\"\n"
    )


def generate_platform_launcher(
        target_dir: Path | None = None,
        python_executable: str | None = None,
        controller_script: Path | None = None,
        system_name: str | None = None) -> Path:
    """Generate a launcher script for the current platform and return its path."""
    output_path = launcher_output_path(target_dir=target_dir, system_name=system_name)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        launcher_script_text(
            python_executable=python_executable,
            controller_script=controller_script,
            system_name=system_name,
        ),
        encoding="utf-8",
    )

    if (system_name or platform.system()) != "Windows":
        current_mode = output_path.stat().st_mode
        output_path.chmod(current_mode | 0o755)

    return output_path
