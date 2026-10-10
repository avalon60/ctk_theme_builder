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


@pytest.mark.parametrize("label", [{}, {"border_width": 7}, {"border_color": ["red", "blue"]},
                                  {"border_width": 4, "border_color": ["red", "blue"]}])
def test_v6_label_theme_normalisation_preserves_existing_values(label):
    """Preserve existing borders while removing only the label legacy colour."""
    from ctk_tb.utils.theme_compat import backfill_text_color_disabled, normalise_label_theme

    original = dict(label)
    theme = {"CTkLabel": dict(label, text_color="white", text_color_disabled="grey"),
             "CTkButton": {"text_color": "black"}, "provenance": {"name": "Test"}}
    normalise_label_theme(theme)
    backfill_text_color_disabled(theme)
    assert theme["CTkLabel"]["border_width"] == original.get("border_width", 0)
    assert theme["CTkLabel"]["border_color"] == original.get("border_color", ["#979DA2", "#565B5E"])
    assert "text_color_disabled" not in theme["CTkLabel"]
    assert theme["CTkButton"]["text_color_disabled"] == "black"
    assert theme["provenance"] == {"name": "Test"}


@pytest.mark.parametrize("kind,prop,new,old", [("geometry", "border_width", 20, 0),
                                              ("colour", "border_color", "red", "blue")])
def test_label_border_commands_undo_redo(monkeypatch, kind, prop, new, old):
    """Keep border changes reversible through the existing preview protocol."""
    import ctk_tb.model.ctk_theme_builder as model

    commands = []
    monkeypatch.setattr(model, "send_command_json", lambda **kwargs: commands.append(kwargs))
    stack = model.CommandStack()
    command = "update_widget_geometry" if kind == "geometry" else "update_widget_colour"
    vector = model.PropertyVector(command_type=kind, command=command, component_type="CTkLabel",
                                  component_property=prop, new_value=new, old_value=old)
    stack.exec_command(vector)
    stack.undo_command()
    stack.redo_command()
    assert [item["parameters"] for item in commands] == [["CTkLabel", prop, value] for value in (new, old, new)]
    assert all(item["command"] == command for item in commands)


@pytest.mark.parametrize("width", [0, 1, 20])
def test_preview_label_border_commands_reach_all_labels(width):
    """Apply received border changes to every registered preview label."""
    from types import SimpleNamespace
    from ctk_tb.view.ctk_theme_preview import PreviewPanel

    class Label:
        def __init__(self):
            self.values = {}

        def configure(self, **kwargs):
            self.values.update(kwargs)

    labels = [Label(), Label(), Label()]
    panel = SimpleNamespace(_rendered_widgets={"CTkLabel": labels},
                            _command_json={"command": "update_widget_geometry",
                                           "parameters": ["CTkLabel", "border_width", width]})
    PreviewPanel._exec_geometry_command(panel)
    for colour in ("#112233", "#aabbcc"):
        PreviewPanel.update_widget_colour(panel, "CTkLabel", "border_color", colour)
        assert all(label.values == {"border_width": width, "border_color": colour} for label in labels)


def test_label_geometry_save_records_old_value_and_persists(tmp_path):
    """Save the width through the geometry dialogue and its command stack."""
    import json
    from types import SimpleNamespace
    from ctk_tb.view.geometry_dialog import GeometryDialog

    vectors = []
    closed = []
    theme = {"CTkLabel": {"border_width": 0}}
    work = tmp_path / "theme.json"
    master = SimpleNamespace(json_state="clean", wip_json=work, set_option_states=lambda: None)
    dialog = SimpleNamespace(geometry_edit_values={"border_width": 20}, master=master,
                             theme_json_data=theme, command_stack=SimpleNamespace(exec_command=lambda property_vector: vectors.append(property_vector)),
                             close_geometry_dialog=lambda: closed.append(True))
    GeometryDialog.save_geometry_edits(dialog, "CTkLabel")
    assert vectors[0].old_value == 0
    assert vectors[0].new_value == 20
    assert json.loads(work.read_text())["CTkLabel"]["border_width"] == 20
    assert master.json_state == "dirty"
    assert closed == [True]


def test_preview_frame_caption_stays_borderless():
    """Keep the shared Top/Base caption outside label border geometry updates."""
    from types import SimpleNamespace
    from ctk_tb.view.ctk_theme_preview import PreviewPanel

    class Label:
        def __init__(self):
            self.width = 0

        def configure(self, border_width):
            self.width = border_width

    caption, sample = Label(), Label()
    panel = SimpleNamespace(lbl_preview_heading=caption,
                            _rendered_widgets={"CTkLabel": [caption, sample]},
                            _command_json={"command": "update_widget_geometry",
                                           "parameters": ["CTkLabel", "border_width", 20]})
    PreviewPanel._exec_geometry_command(panel)
    assert caption.width == 0
    assert sample.width == 20


def test_scaffold_fills_missing_widgets_properties_and_nested_font_defaults():
    """Use arbitrary scaffold additions without adding widget-specific code."""
    from ctk_tb.utils.theme_compat import normalise_theme

    scaffold = {"CTkEntry": {"border_width": 2, "new_colour": ["red", "blue"]},
                "CTkFutureWidget": {"new_width": 3}, "CTkFont": {"Linux": {"size": 13}},
                "provenance": {"name": "Default"}}
    theme = {"CTkEntry": {"border_width": 9, "custom": "keep"},
             "CTkFont": {"Linux": {"family": "Custom"}}, "provenance": {"name": "Original"}}
    normalise_theme(theme, scaffold)
    assert theme["CTkEntry"] == {"border_width": 9, "custom": "keep", "new_colour": ["red", "blue"]}
    assert theme["CTkFutureWidget"] == {"new_width": 3}
    assert theme["CTkFont"]["Linux"] == {"family": "Custom", "size": 13}
    assert theme["provenance"] == {"name": "Original"}
    theme["CTkEntry"]["new_colour"][0] = "green"
    assert scaffold["CTkEntry"]["new_colour"][0] == "red"
    import copy

    before = copy.deepcopy(theme)
    normalise_theme(theme, scaffold)
    assert theme == before


def test_scaffold_contains_renderable_defaults():
    """Keep the shipped widget scaffold free of null colour placeholders."""
    import json
    from ctk_tb.paths import ETC_DIR
    from ctk_tb.utils.theme_compat import normalise_theme

    theme = {}
    normalise_theme(theme)
    assert "provenance" not in theme
    assert "null" not in json.dumps(theme)
    assert theme["CTkLabel"]["border_width"] == 0
    assert theme["CTkLabel"]["border_color"] == ["#979DA2", "#565B5E"]
    assert theme["CTkButton"]["border_width"] == json.loads((ETC_DIR / "theme_skeleton.json").read_text())["CTkButton"]["border_width"]


def test_scaffold_rejects_malformed_widget_sections():
    """Reject invalid sections instead of replacing user-owned values."""
    from ctk_tb.utils.theme_compat import normalise_theme

    with pytest.raises(ValueError, match="CTkLabel"):
        normalise_theme({"CTkLabel": "invalid"}, {"CTkLabel": {"border_width": 0}})
