import plistlib
import shutil
import sys

import pytest

import ctk_tb.paths as app_paths
from ctk_tb.model.ctk_theme_builder import scaling_float, ui_scaling_list
from ctk_tb.utils import cbtk_kit as cbtk
from ctk_tb.utils import launcher_generator
from ctk_tb.utils.launcher_generator import MACOS_ICON_FILENAME, generate_platform_launcher


def test_scaling_float_converts_percent_to_float():
    assert scaling_float("70%") == 0.7
    assert scaling_float("100%") == 1.0
    assert scaling_float("130%") == 1.3


def test_ui_scaling_list_matches_supported_values():
    assert ui_scaling_list() == ["70%", "80%", "90%", "100%", "110%", "120%", "130%"]


def test_colour_helpers_accept_bare_hex_strings():
    assert cbtk.contrast_colour("0e1d28") == "#220914"
    assert cbtk.shade_up("0e1d28", differential=10) == "#182732"
    assert cbtk.shade_down("0e1d28", differential=10) == "#04131e"


def test_macos_launcher_contains_its_icon(tmp_path):
    launcher = generate_platform_launcher(
        target_dir=tmp_path,
        python_executable=sys.executable,
        system_name="Darwin",
    )
    contents = launcher.launcher_path / "Contents"
    info = plistlib.loads((contents / "Info.plist").read_bytes())
    icon_path = contents / "Resources" / MACOS_ICON_FILENAME

    assert info["CFBundleIconFile"] == MACOS_ICON_FILENAME
    assert launcher.launcher_path.parent.name == launcher_generator.MACOS_STAGING_DIRECTORY
    assert icon_path.read_bytes() == (app_paths.APP_IMAGES / MACOS_ICON_FILENAME).read_bytes()


def test_macos_desktop_shortcut_points_to_applications_copy(tmp_path, monkeypatch):
    monkeypatch.setattr(launcher_generator, "applications_menu_dir", lambda _system: tmp_path / "Applications")
    monkeypatch.setattr(launcher_generator, "desktop_dir", lambda _system: tmp_path / "Desktop")
    launcher = generate_platform_launcher(
        target_dir=tmp_path / "launchers",
        python_executable=sys.executable,
        system_name="Darwin",
    )

    with pytest.raises(launcher_generator.LauncherGenerationError, match="Install to Applications Folder"):
        launcher_generator.create_desktop_shortcut(launcher)

    installed = launcher_generator.install_to_applications_menu(launcher)
    desktop_shortcut = launcher_generator.create_desktop_shortcut(launcher)
    legacy_path = tmp_path / "launchers" / launcher_generator.MACOS_APP_BUNDLE_NAME
    shutil.copytree(launcher.launcher_path, legacy_path)
    launcher_generator.generate_platform_launcher(
        target_dir=tmp_path / "launchers",
        python_executable=sys.executable,
        system_name="Darwin",
    )
    assert launcher_generator.install_to_applications_menu(launcher) == installed
    assert launcher_generator.create_desktop_shortcut(launcher) == desktop_shortcut

    assert desktop_shortcut.is_symlink()
    assert desktop_shortcut.resolve() == installed.resolve()
    assert list((tmp_path / "Applications").glob("*.app")) == [installed]
    assert list((tmp_path / "Desktop").glob("*.app")) == [desktop_shortcut]
    assert list((tmp_path / "launchers" / ".generated").glob("*.app")) == [launcher.launcher_path]
    assert not legacy_path.exists()
    assert (tmp_path / "launchers" / ".generated" / "CTk Theme Builder.legacy").is_dir()
