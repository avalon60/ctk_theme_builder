from ctk_tb.model.ctk_theme_builder import scaling_float, ui_scaling_list
from ctk_tb.utils import cbtk_kit as cbtk


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
