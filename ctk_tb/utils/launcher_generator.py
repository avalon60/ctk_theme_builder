"""Generate convenience launchers for the current platform."""

# Author: Clive Bostock
# Date: 2026-04-12
# Description: Creates platform-specific launchers and Linux desktop integration files.

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
import platform
import re
import shlex
import shutil
import sys
from pathlib import Path

import ctk_tb.paths as app_paths

APPLICATIONS_MENU_DIR = Path.home() / ".local" / "share" / "applications"
DESKTOP_DIR = Path.home() / "Desktop"
LINUX_DESKTOP_FILENAME = "ctk-theme-builder.desktop"
LINUX_RUNNER_FILENAME = "ctk-theme-builder.sh"
MACOS_LAUNCHER_FILENAME = "ctk-theme-builder.command"
WINDOWS_LAUNCHER_FILENAME = "ctk-theme-builder.bat"


class LauncherGenerationError(RuntimeError):
    """Raised when launcher generation or installation fails."""


@dataclass(frozen=True)
class LauncherBundle:
    """Represents the generated launcher artefacts for the current platform."""

    system_name: str
    python_executable: Path
    controller_script: Path
    launcher_path: Path
    generated_at: str
    app_version: str
    runner_script_path: Path | None = None


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
    """Return the launcher generation timestamp."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _validate_generation_paths(python_executable: Path, controller_script: Path) -> None:
    """Validate generation inputs before writing any launcher files."""
    if not python_executable.exists() or not os.access(python_executable, os.X_OK):
        raise LauncherGenerationError(
            f"Python interpreter path is invalid or not executable: {python_executable}"
        )
    if not controller_script.exists():
        raise LauncherGenerationError(
            f"CTk Theme Builder controller script not found: {controller_script}"
        )


def _set_executable(path: Path) -> None:
    """Ensure a file is executable."""
    try:
        current_mode = path.stat().st_mode
        path.chmod(current_mode | 0o755)
    except PermissionError as exc:
        raise LauncherGenerationError(
            f"Unable to update permissions for {path}: {exc}"
        ) from exc


def _header_lines(comment_prefix: str, generated_at: str, python_executable: Path, app_version: str) -> str:
    """Return standard launcher metadata header lines."""
    return (
        f"{comment_prefix} CTk Theme Builder Launcher\n"
        f"{comment_prefix} Generated: {generated_at}\n"
        f"{comment_prefix} Python: {python_executable}\n"
        f"{comment_prefix} Version: {app_version}\n"
    )


def _linux_runner_text(python_executable: Path, controller_script: Path, generated_at: str, app_version: str) -> str:
    quoted_python = shlex.quote(str(python_executable))
    quoted_controller = shlex.quote(str(controller_script))
    return (
        "#!/usr/bin/env bash\n"
        f"{_header_lines('#', generated_at, python_executable, app_version)}"
        "PYTHON_EXE="
        f"{quoted_python}\n"
        "CTK_THEME_BUILDER="
        f"{quoted_controller}\n\n"
        'if [ ! -x "$PYTHON_EXE" ]; then\n'
        '  echo "Python interpreter not found. Please regenerate this launcher via CTk Theme Builder."\n'
        "  exit 1\n"
        "fi\n\n"
        'if [ ! -f "$CTK_THEME_BUILDER" ]; then\n'
        '  echo "CTk Theme Builder entry point not found. Please regenerate this launcher via CTk Theme Builder."\n'
        "  exit 1\n"
        "fi\n\n"
        'exec "$PYTHON_EXE" "$CTK_THEME_BUILDER" "$@"\n'
    )


def _linux_desktop_text(runner_script: Path, generated_at: str, python_executable: Path, app_version: str) -> str:
    quoted_runner = shlex.quote(str(runner_script))
    return (
        f"{_header_lines('#', generated_at, python_executable, app_version)}"
        "[Desktop Entry]\n"
        "Version=1.0\n"
        "Type=Application\n"
        "Name=CTk Theme Builder\n"
        "Comment=Launch CTk Theme Builder\n"
        f"Exec={quoted_runner}\n"
        "Terminal=false\n"
        "Categories=Development;\n"
    )


def _macos_launcher_text(python_executable: Path, controller_script: Path, generated_at: str, app_version: str) -> str:
    quoted_python = shlex.quote(str(python_executable))
    quoted_controller = shlex.quote(str(controller_script))
    return (
        "#!/usr/bin/env bash\n"
        f"{_header_lines('#', generated_at, python_executable, app_version)}"
        "PYTHON_EXE="
        f"{quoted_python}\n"
        "CTK_THEME_BUILDER="
        f"{quoted_controller}\n\n"
        'if [ ! -x "$PYTHON_EXE" ]; then\n'
        '  echo "Python interpreter not found. Please regenerate this launcher via CTk Theme Builder."\n'
        "  exit 1\n"
        "fi\n\n"
        'if [ ! -f "$CTK_THEME_BUILDER" ]; then\n'
        '  echo "CTk Theme Builder entry point not found. Please regenerate this launcher via CTk Theme Builder."\n'
        "  exit 1\n"
        "fi\n\n"
        'exec "$PYTHON_EXE" "$CTK_THEME_BUILDER" "$@"\n'
    )


def _windows_launcher_text(
        python_executable: Path,
        controller_script: Path,
        generated_at: str,
        app_version: str) -> str:
    return (
        "@echo off\n"
        f"{_header_lines('::', generated_at, python_executable, app_version)}"
        f"set \"PYTHON_EXE={python_executable}\"\n"
        f"set \"CTK_THEME_BUILDER={controller_script}\"\n\n"
        "if not exist \"%PYTHON_EXE%\" (\n"
        "  echo Python interpreter not found. Please regenerate this launcher via CTk Theme Builder.\n"
        "  exit /b 1\n"
        ")\n\n"
        "if not exist \"%CTK_THEME_BUILDER%\" (\n"
        "  echo CTk Theme Builder entry point not found. Please regenerate this launcher via CTk Theme Builder.\n"
        "  exit /b 1\n"
        ")\n\n"
        "\"%PYTHON_EXE%\" \"%CTK_THEME_BUILDER%\" %*\n"
        "if errorlevel 1 exit /b %errorlevel%\n"
    )


def _write_text_file(path: Path, content: str) -> None:
    """Write a text file with UTF-8 encoding."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise LauncherGenerationError(f"Unable to write launcher file {path}: {exc}") from exc


def generate_platform_launcher(
        target_dir: Path | None = None,
        python_executable: str | None = None,
        controller_script: Path | None = None,
        system_name: str | None = None) -> LauncherBundle:
    """Generate the launcher artefacts for the current or specified platform."""
    target_dir = target_dir or app_paths.LAUNCHERS_DIR
    system_name = system_name or platform.system()
    python_path = Path(python_executable or sys.executable).expanduser().resolve()
    controller_path = (controller_script or (app_paths.PACKAGE_DIR / "controller" / "ctk_theme_builder.py")).resolve()
    generated_at = _generation_timestamp()
    app_version = _application_version()

    _validate_generation_paths(python_path, controller_path)

    if system_name == "Linux":
        runner_path = target_dir / LINUX_RUNNER_FILENAME
        desktop_path = target_dir / LINUX_DESKTOP_FILENAME
        _write_text_file(
            runner_path,
            _linux_runner_text(
                python_executable=python_path,
                controller_script=controller_path,
                generated_at=generated_at,
                app_version=app_version,
            ),
        )
        _write_text_file(
            desktop_path,
            _linux_desktop_text(
                runner_script=runner_path,
                generated_at=generated_at,
                python_executable=python_path,
                app_version=app_version,
            ),
        )
        _set_executable(runner_path)
        _set_executable(desktop_path)
        return LauncherBundle(
            system_name=system_name,
            python_executable=python_path,
            controller_script=controller_path,
            launcher_path=desktop_path,
            runner_script_path=runner_path,
            generated_at=generated_at,
            app_version=app_version,
        )

    if system_name == "Darwin":
        launcher_path = target_dir / MACOS_LAUNCHER_FILENAME
        _write_text_file(
            launcher_path,
            _macos_launcher_text(
                python_executable=python_path,
                controller_script=controller_path,
                generated_at=generated_at,
                app_version=app_version,
            ),
        )
        _set_executable(launcher_path)
        return LauncherBundle(
            system_name=system_name,
            python_executable=python_path,
            controller_script=controller_path,
            launcher_path=launcher_path,
            generated_at=generated_at,
            app_version=app_version,
        )

    launcher_path = target_dir / WINDOWS_LAUNCHER_FILENAME
    _write_text_file(
        launcher_path,
        _windows_launcher_text(
            python_executable=python_path,
            controller_script=controller_path,
            generated_at=generated_at,
            app_version=app_version,
        ),
    )
    return LauncherBundle(
        system_name=system_name,
        python_executable=python_path,
        controller_script=controller_path,
        launcher_path=launcher_path,
        generated_at=generated_at,
        app_version=app_version,
    )


def install_to_applications_menu(launcher_bundle: LauncherBundle) -> Path:
    """Install the generated Linux desktop entry into the user applications menu."""
    if launcher_bundle.system_name != "Linux":
        raise LauncherGenerationError("Applications menu installation is supported on Linux only.")

    target_path = APPLICATIONS_MENU_DIR / LINUX_DESKTOP_FILENAME
    try:
        APPLICATIONS_MENU_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(launcher_bundle.launcher_path, target_path)
    except OSError as exc:
        raise LauncherGenerationError(
            f"Unable to install launcher to the applications menu: {exc}"
        ) from exc
    _set_executable(target_path)
    return target_path


def create_desktop_shortcut(launcher_bundle: LauncherBundle) -> Path:
    """Install the generated Linux desktop entry onto the user's desktop."""
    if launcher_bundle.system_name != "Linux":
        raise LauncherGenerationError("Desktop shortcut creation is supported on Linux only.")

    target_path = DESKTOP_DIR / LINUX_DESKTOP_FILENAME
    try:
        DESKTOP_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(launcher_bundle.launcher_path, target_path)
    except OSError as exc:
        raise LauncherGenerationError(
            f"Unable to create desktop shortcut: {exc}"
        ) from exc
    _set_executable(target_path)
    return target_path
