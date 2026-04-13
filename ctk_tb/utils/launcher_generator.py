"""Generate convenience launchers for the current platform."""

# Author: Clive Bostock
# Date: 2026-04-12
# Description: Creates platform-specific launchers and Linux desktop integration files.

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
import platform
import plistlib
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import ctk_tb.paths as app_paths

LINUX_DESKTOP_FILENAME = "ctk-theme-builder.desktop"
LINUX_RUNNER_FILENAME = "ctk-theme-builder.sh"
MACOS_APP_BUNDLE_NAME = "CTk Theme Builder.app"
MACOS_BUNDLE_EXECUTABLE = "ctk-theme-builder"
WINDOWS_LAUNCHER_FILENAME = "ctk-theme-builder.bat"
WINDOWS_SHORTCUT_FILENAME = "CTk Theme Builder.lnk"
WINDOWS_ICON_FILENAME = "ctk-tb-ico.ico"
LINUX_ICON_FILENAME = "ctk-tb-ico-256.png"


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


def applications_menu_dir(system_name: str) -> Path:
    """Return the user-writable applications/start-menu directory for a platform."""
    if system_name == "Linux":
        return Path.home() / ".local" / "share" / "applications"
    if system_name == "Darwin":
        return Path.home() / "Applications"

    appdata = os.getenv("APPDATA")
    if appdata:
        return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    return Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs"


def desktop_dir(system_name: str) -> Path:
    """Return the user desktop directory for a platform."""
    if system_name == "Windows":
        userprofile = os.getenv("USERPROFILE")
        if userprofile:
            return Path(userprofile) / "Desktop"
    return Path.home() / "Desktop"


def applications_menu_label(system_name: str) -> str:
    """Return the user-facing applications action label for a platform."""
    if system_name == "Linux":
        return "Install to Applications Menu"
    if system_name == "Darwin":
        return "Install to Applications Folder"
    return "Install to Start Menu"


def desktop_shortcut_label(system_name: str) -> str:
    """Return the user-facing desktop action label for a platform."""
    if system_name == "Darwin":
        return "Create Desktop App"
    if system_name == "Windows":
        return "Create Desktop Launcher"
    return "Create Desktop Shortcut"


def applications_menu_target_path(launcher_bundle: LauncherBundle) -> Path:
    """Return the platform-appropriate target path for application-menu installation."""
    if launcher_bundle.system_name == "Windows":
        return applications_menu_dir(launcher_bundle.system_name) / WINDOWS_SHORTCUT_FILENAME
    return applications_menu_dir(launcher_bundle.system_name) / launcher_bundle.launcher_path.name


def desktop_shortcut_target_path(launcher_bundle: LauncherBundle) -> Path:
    """Return the platform-appropriate target path for desktop shortcut installation."""
    if launcher_bundle.system_name == "Windows":
        return desktop_dir(launcher_bundle.system_name) / WINDOWS_SHORTCUT_FILENAME
    return desktop_dir(launcher_bundle.system_name) / launcher_bundle.launcher_path.name


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


def _package_root(controller_script: Path) -> Path:
    """Return the import root that contains the ``ctk_tb`` package."""
    return controller_script.resolve().parent.parent.parent


def _linux_runner_text(python_executable: Path, controller_script: Path, generated_at: str, app_version: str) -> str:
    quoted_python = shlex.quote(str(python_executable))
    quoted_controller = shlex.quote(str(controller_script))
    quoted_package_root = shlex.quote(str(_package_root(controller_script)))
    return (
        "#!/usr/bin/env bash\n"
        f"{_header_lines('#', generated_at, python_executable, app_version)}"
        "PYTHON_EXE="
        f"{quoted_python}\n"
        "CTK_THEME_BUILDER="
        f"{quoted_controller}\n"
        "PACKAGE_ROOT="
        f"{quoted_package_root}\n\n"
        'if [ ! -x "$PYTHON_EXE" ]; then\n'
        '  echo "Python interpreter not found. Please regenerate this launcher via CTk Theme Builder."\n'
        "  exit 1\n"
        "fi\n\n"
        'if [ ! -f "$CTK_THEME_BUILDER" ]; then\n'
        '  echo "CTk Theme Builder entry point not found. Please regenerate this launcher via CTk Theme Builder."\n'
        "  exit 1\n"
        "fi\n\n"
        'if [ -n "$PYTHONPATH" ]; then\n'
        '  export PYTHONPATH="$PACKAGE_ROOT:$PYTHONPATH"\n'
        "else\n"
        '  export PYTHONPATH="$PACKAGE_ROOT"\n'
        "fi\n\n"
        'exec "$PYTHON_EXE" "$CTK_THEME_BUILDER" "$@"\n'
    )


def _linux_desktop_text(
        runner_script: Path,
        icon_path: Path,
        generated_at: str,
        python_executable: Path,
        app_version: str) -> str:
    quoted_runner = shlex.quote(str(runner_script))
    return (
        f"{_header_lines('#', generated_at, python_executable, app_version)}"
        "[Desktop Entry]\n"
        "Version=1.0\n"
        "Type=Application\n"
        "Name=CTk Theme Builder\n"
        "Comment=Launch CTk Theme Builder\n"
        f"Exec={quoted_runner}\n"
        f"Icon={icon_path}\n"
        "Terminal=false\n"
        "Categories=Development;\n"
    )


def _macos_launcher_text(python_executable: Path, controller_script: Path, generated_at: str, app_version: str) -> str:
    quoted_python = shlex.quote(str(python_executable))
    quoted_controller = shlex.quote(str(controller_script))
    quoted_package_root = shlex.quote(str(_package_root(controller_script)))
    return (
        "#!/usr/bin/env bash\n"
        f"{_header_lines('#', generated_at, python_executable, app_version)}"
        "PYTHON_EXE="
        f"{quoted_python}\n"
        "CTK_THEME_BUILDER="
        f"{quoted_controller}\n"
        "PACKAGE_ROOT="
        f"{quoted_package_root}\n\n"
        'if [ ! -x "$PYTHON_EXE" ]; then\n'
        '  echo "Python interpreter not found. Please regenerate this launcher via CTk Theme Builder."\n'
        "  exit 1\n"
        "fi\n\n"
        'if [ ! -f "$CTK_THEME_BUILDER" ]; then\n'
        '  echo "CTk Theme Builder entry point not found. Please regenerate this launcher via CTk Theme Builder."\n'
        "  exit 1\n"
        "fi\n\n"
        'if [ -n "$PYTHONPATH" ]; then\n'
        '  export PYTHONPATH="$PACKAGE_ROOT:$PYTHONPATH"\n'
        "else\n"
        '  export PYTHONPATH="$PACKAGE_ROOT"\n'
        "fi\n\n"
        'exec "$PYTHON_EXE" "$CTK_THEME_BUILDER" "$@"\n'
    )


def _windows_launcher_text(
        python_executable: Path,
        controller_script: Path,
        generated_at: str,
        app_version: str) -> str:
    package_root = _package_root(controller_script)
    return (
        "@echo off\n"
        f"{_header_lines('::', generated_at, python_executable, app_version)}"
        f"set \"PYTHON_EXE={python_executable}\"\n"
        f"set \"CTK_THEME_BUILDER={controller_script}\"\n\n"
        f"set \"PACKAGE_ROOT={package_root}\"\n\n"
        "if not exist \"%PYTHON_EXE%\" (\n"
        "  echo Python interpreter not found. Please regenerate this launcher via CTk Theme Builder.\n"
        "  exit /b 1\n"
        ")\n\n"
        "if not exist \"%CTK_THEME_BUILDER%\" (\n"
        "  echo CTk Theme Builder entry point not found. Please regenerate this launcher via CTk Theme Builder.\n"
        "  exit /b 1\n"
        ")\n\n"
        "if defined PYTHONPATH (\n"
        "  set \"PYTHONPATH=%PACKAGE_ROOT%;%PYTHONPATH%\"\n"
        ") else (\n"
        "  set \"PYTHONPATH=%PACKAGE_ROOT%\"\n"
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


def _write_binary_file(path: Path, content: bytes) -> None:
    """Write a binary file."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    except OSError as exc:
        raise LauncherGenerationError(f"Unable to write launcher file {path}: {exc}") from exc


def _macos_info_plist(app_version: str) -> bytes:
    """Return Info.plist content for a lightweight macOS app bundle."""
    plist_data = {
        "CFBundleDevelopmentRegion": "en",
        "CFBundleExecutable": MACOS_BUNDLE_EXECUTABLE,
        "CFBundleIdentifier": "org.avalon60.ctk-theme-builder.launcher",
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": "CTk Theme Builder",
        "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": app_version,
        "CFBundleVersion": app_version,
        "LSMinimumSystemVersion": "10.13",
    }
    return plistlib.dumps(plist_data)


def _copy_launcher_artifact(source_path: Path, target_path: Path, system_name: str) -> Path:
    """Copy a launcher file or bundle to its final destination."""
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.exists():
            if target_path.is_dir():
                shutil.rmtree(target_path)
            else:
                target_path.unlink()

        if source_path.is_dir():
            shutil.copytree(source_path, target_path)
        else:
            shutil.copy2(source_path, target_path)
    except OSError as exc:
        raise LauncherGenerationError(f"Unable to copy launcher to {target_path}: {exc}") from exc

    if system_name in {"Linux", "Darwin"}:
        if target_path.is_dir():
            executable_path = target_path / "Contents" / "MacOS" / MACOS_BUNDLE_EXECUTABLE
            if executable_path.exists():
                _set_executable(executable_path)
        else:
            _set_executable(target_path)
    return target_path


def _create_windows_shortcut(target_path: Path, launcher_path: Path, icon_path: Path) -> Path:
    """Create a Windows .lnk shortcut pointing at the generated batch launcher."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if target_path.exists():
        target_path.unlink()

    working_directory = str(launcher_path.parent)
    powershell_script = (
        "$WshShell = New-Object -ComObject WScript.Shell; "
        f"$Shortcut = $WshShell.CreateShortcut('{str(target_path)}'); "
        f"$Shortcut.TargetPath = '{str(launcher_path)}'; "
        f"$Shortcut.WorkingDirectory = '{working_directory}'; "
        f"$Shortcut.IconLocation = '{str(icon_path)},0'; "
        "$Shortcut.Save()"
    )

    for executable in ("powershell.exe", "pwsh.exe"):
        try:
            subprocess.run(
                [executable, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", powershell_script],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
            return target_path
        except FileNotFoundError:
            continue
        except subprocess.CalledProcessError as exc:
            raise LauncherGenerationError(
                f"Unable to create Windows shortcut via {executable}: {exc.stderr.strip()}"
            ) from exc

    raise LauncherGenerationError("Unable to create Windows shortcut: PowerShell is not available.")


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
        icon_path = (app_paths.APP_IMAGES / LINUX_ICON_FILENAME).resolve()
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
                icon_path=icon_path,
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
        launcher_path = target_dir / MACOS_APP_BUNDLE_NAME
        executable_path = launcher_path / "Contents" / "MacOS" / MACOS_BUNDLE_EXECUTABLE
        info_plist_path = launcher_path / "Contents" / "Info.plist"
        _write_text_file(
            executable_path,
            _macos_launcher_text(
                python_executable=python_path,
                controller_script=controller_path,
                generated_at=generated_at,
                app_version=app_version,
            ),
        )
        _write_binary_file(info_plist_path, _macos_info_plist(app_version))
        _set_executable(executable_path)
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
    """Install the generated launcher into the user applications/start-menu location."""
    target_path = applications_menu_target_path(launcher_bundle)
    if launcher_bundle.system_name == "Windows":
        icon_path = (app_paths.APP_IMAGES / WINDOWS_ICON_FILENAME).resolve()
        return _create_windows_shortcut(target_path, launcher_bundle.launcher_path, icon_path)
    return _copy_launcher_artifact(launcher_bundle.launcher_path, target_path, launcher_bundle.system_name)


def create_desktop_shortcut(launcher_bundle: LauncherBundle) -> Path:
    """Install the generated launcher onto the user's desktop."""
    target_path = desktop_shortcut_target_path(launcher_bundle)
    if launcher_bundle.system_name == "Windows":
        icon_path = (app_paths.APP_IMAGES / WINDOWS_ICON_FILENAME).resolve()
        return _create_windows_shortcut(target_path, launcher_bundle.launcher_path, icon_path)
    return _copy_launcher_artifact(launcher_bundle.launcher_path, target_path, launcher_bundle.system_name)
