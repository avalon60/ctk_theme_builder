"""CustomTkinter, V4 -> V5 Theme Migrator"""
# Control
__title__ = 'CustomTkinter Theme Migrator'
__author__ = 'Clive Bostock'
__version__ = "1.0.0"

import argparse
from operator import attrgetter
from argparse import HelpFormatter
from pathlib import Path
import json
import os
from os.path import exists
from os.path import expanduser
import shutil

prog_path = os.path.realpath(__file__)
prog = os.path.basename(__file__)

app_home = Path(os.path.dirname(os.path.realpath(__file__)))


class SortingHelpFormatter(HelpFormatter):
    def add_arguments(self, actions):
        actions = sorted(actions, key=attrgetter('option_strings'))
        super(SortingHelpFormatter, self).add_arguments(actions)


ap = argparse.ArgumentParser(formatter_class=SortingHelpFormatter
                             , description=f"""{prog}: The ctk_theme_migrator tool, is designed to migrate
                             the CustomTkinter v4 JSON, to the V5 format.""")

ap.add_argument("-i", "--input-theme-file", required=False, action="store",
                help=f'Specifies the pathname of the v4 input JSON file to be converted.) ',
                dest='input_theme_file')

ap.add_argument("-o", "--output-theme-file", required=False, action="store",
                help=f'Specifies the pathname of the JSON file to output file to be converted to v5.) ',
                dest='output_theme_file')

ap.add_argument("-s", "--strict", required=False, action="store_true", dest="retain_window_bg",
                help=f"Retains the original window_bg_color. This doesn't always look good with some app designs."
                     f"If omitted, the frame_low colour is substituted.")

args_list = vars(ap.parse_args())

input_theme_file = args_list["input_theme_file"]
output_theme_file = args_list["output_theme_file"]
retain_window_bg = args_list["retain_window_bg"]

if not exists(input_theme_file):
    print(f'ERROR: Cannot open file: {input_theme_file}')
    print('Please check/correct the file pathname and / or permissions.')
    exit(1)

class ThemeConverter:
    def __init__(self, application_home: Path, theme_file_in: Path, theme_file_out: Path, strict=bool):
        etc = application_home / 'assets' / 'etc'
        self.skeleton_json = etc / 'theme_skeleton.json'
        self.theme_file_in = os.path.abspath(theme_file_in)
        self.theme_file_out = os.path.abspath(theme_file_out)
        self.json_theme_v4 = {}
        self.json_theme_v5 = {}
        self.strict = strict


    def load_theme(self):
        """This method not only loads the V4 input theme file, but also the V5 skeleton, which we populate as a
        starting point for our V5 output JSON."""
        with open(self.theme_file_in) as json_file:
            try:
                self.json_theme_v4 = json.load(json_file)
            except ValueError:
                print(f'The file, "{json_file}", does not appear to be a valid '
                      f'theme file (JSON parse error).')
                exit(1)
            except IOError:
                print(f'Failed to read theme file {self.theme_file_out} - possible permissions issue.')
                exit(1)

        with open(self.skeleton_json) as json_file:
            try:
                self.json_theme_v5 = json.load(json_file)
            except ValueError:
                print(f'The file, "{self.skeleton_json}", does not appear to be a valid '
                      f'theme file (JSON parse error).')
                exit(1)
            except IOError:
                print(f'Failed to read theme file {self.skeleton_json} - possible permissions issue.')
                exit(1)

    def convert_json(self):
        # CTk
        if self.strict:
            self.json_theme_v5["CTk"]["fg_color"] = self.json_theme_v4["color"]["window_bg_color"]
        else:
            self.json_theme_v5 ["CTk"]["fg_color"] = self.json_theme_v4["color"]["frame_low"]

        # CTkTopLevel
        self.json_theme_v5["CTkToplevel"]["fg_color"] = self.json_theme_v4["color"]["frame_low"]

        # CTkFrame
        self.json_theme_v5["CTkFrame"]["fg_color"] = self.json_theme_v4["color"]["frame_low"]
        self.json_theme_v5["CTkFrame"]["top_fg_color"] = self.json_theme_v4["color"]["frame_high"]
        self.json_theme_v5["CTkFrame"]["border_color"] = self.json_theme_v4["color"]["frame_border"]

        # CTkButton
        self.json_theme_v5["CTkButton"]["fg_color"] = self.json_theme_v4["color"]["button"]
        self.json_theme_v5["CTkButton"]["hover_color"] = self.json_theme_v4["color"]["button_hover"]
        self.json_theme_v5["CTkButton"]["border_color"] = self.json_theme_v4["color"]["button_border"]
        self.json_theme_v5["CTkButton"]["text_color"] = self.json_theme_v4["color"]["text"]
        self.json_theme_v5["CTkButton"]["text_color_disabled"] = self.json_theme_v4["color"]["text_disabled"]

        # CTkLabel
        self.json_theme_v5["CTkLabel"]["fg_color"] = "transparent"
        self.json_theme_v5["CTkLabel"]["text_color"] = self.json_theme_v4["color"]["text"]

        # CTkEntry
        self.json_theme_v5["CTkEntry"]["fg_color"] = self.json_theme_v4["color"]["entry"]
        self.json_theme_v5["CTkEntry"]["border_color"] = self.json_theme_v4["color"]["entry_border"]
        self.json_theme_v5["CTkEntry"]["text_color"] = self.json_theme_v4["color"]["text"]
        self.json_theme_v5["CTkEntry"]["placeholder_text_color"] = self.json_theme_v4["color"]["entry_placeholder_text"]

        # CTkCheckbox
        self.json_theme_v5["CTkCheckbox"]["fg_color"] = self.json_theme_v4["color"]["button"]
        self.json_theme_v5["CTkCheckbox"]["border_color"] = self.json_theme_v4["color"]["checkbox_border"]
        self.json_theme_v5["CTkCheckbox"]["hover_color"] = self.json_theme_v4["color"]["button_hover"]
        self.json_theme_v5["CTkCheckbox"]["checkmark_color"] = self.json_theme_v4["color"]["checkmark"]
        self.json_theme_v5["CTkCheckbox"]["text_color"] = self.json_theme_v4["color"]["text"]
        self.json_theme_v5["CTkCheckbox"]["text_color_disabled"] = self.json_theme_v4["color"]["text_disabled"]

        # CTkSwitch
        self.json_theme_v5["CTkSwitch"]["fg_color"] = self.json_theme_v4["color"]["switch"]
        self.json_theme_v5["CTkSwitch"]["progress_color"] = self.json_theme_v4["color"]["switch_progress"]
        self.json_theme_v5["CTkSwitch"]["button_color"] = self.json_theme_v4["color"]["switch_button"]
        self.json_theme_v5["CTkSwitch"]["button_hover_color"] = self.json_theme_v4["color"]["switch_button_hover"]
        self.json_theme_v5["CTkSwitch"]["text_color"] = self.json_theme_v4["color"]["text"]
        self.json_theme_v5["CTkSwitch"]["text_color_disabled"] = self.json_theme_v4["color"]["text_disabled"]

        # CTkRadiobutton
        self.json_theme_v5["CTkRadiobutton"]["fg_color"] = self.json_theme_v4["color"]["button"]
        self.json_theme_v5["CTkRadiobutton"]["border_color"] = self.json_theme_v4["color"]["checkbox_border"]
        self.json_theme_v5["CTkRadiobutton"]["hover_color"] = self.json_theme_v4["color"]["frame_border"]
        self.json_theme_v5["CTkRadiobutton"]["text_color"] = self.json_theme_v4["color"]["switch_button_hover"]
        self.json_theme_v5["CTkRadiobutton"]["text_color_disabled"] = self.json_theme_v4["color"]["text_disabled"]

        # CTkProgressBar
        self.json_theme_v5["CTkProgressBar"]["fg_color"] = self.json_theme_v4["color"]["progressbar"]
        self.json_theme_v5["CTkProgressBar"]["progress_color"] = self.json_theme_v4["color"]["progressbar_progress"]
        self.json_theme_v5["CTkProgressBar"]["border_color"] = self.json_theme_v4["color"]["progressbar_border"]

        # CTkSlider
        self.json_theme_v5["CTkSlider"]["fg_color"] = self.json_theme_v4["color"]["slider"]
        self.json_theme_v5["CTkSlider"]["progress_color"] = self.json_theme_v4["color"]["slider_progress"]
        self.json_theme_v5["CTkSlider"]["button_color"] = self.json_theme_v4["color"]["button"]
        self.json_theme_v5["CTkSlider"]["button_hover_color"] = self.json_theme_v4["color"]["frame_border"]

        # CTkOptionMenu
        self.json_theme_v5["CTkOptionMenu"]["fg_color"] = self.json_theme_v4["color"]["dropdown_color"]
        self.json_theme_v5["CTkOptionMenu"]["button_color"] = self.json_theme_v4["color"]["optionmenu_button"]
        self.json_theme_v5["CTkOptionMenu"]["button_hover_color"] = self.json_theme_v4["color"]["optionmenu_button_hover"]
        self.json_theme_v5["CTkOptionMenu"]["text_color"] = self.json_theme_v4["color"]["dropdown_text"]
        self.json_theme_v5["CTkOptionMenu"]["text_color_disabled"] = self.json_theme_v4["color"]["text_disabled"]

        # CTkComboBox
        self.json_theme_v5["CTkComboBox"]["fg_color"] = self.json_theme_v4["color"]["dropdown_color"]
        self.json_theme_v5["CTkComboBox"]["border_color"] = self.json_theme_v4["color"]["combobox_border"]
        self.json_theme_v5["CTkComboBox"]["button_color"] = self.json_theme_v4["color"]["button"]
        self.json_theme_v5["CTkComboBox"]["button_hover_color"] = self.json_theme_v4["color"]["combobox_button_hover"]
        self.json_theme_v5["CTkComboBox"]["text_color"] = self.json_theme_v4["color"]["text"]
        self.json_theme_v5["CTkComboBox"]["text_color_disabled"] = self.json_theme_v4["color"]["text_disabled"]

        # CTkScrollbar
        self.json_theme_v5["CTkScrollbar"]["fg_color"] = "transparent"
        self.json_theme_v5["CTkScrollbar"]["button_color"] = self.json_theme_v4["color"]["scrollbar_button"]
        self.json_theme_v5["CTkScrollbar"]["button_hover_color"] = self.json_theme_v4["color"]["scrollbar_button_hover"]


        # CTkSegmentedButton
        self.json_theme_v5["CTkSegmentedButton"]["fg_color"] = self.json_theme_v4["color"]["button"]
        self.json_theme_v5["CTkSegmentedButton"]["selected_color"] = self.json_theme_v4["color"]["button_hover"]
        self.json_theme_v5["CTkSegmentedButton"]["selected_hover_color"] = self.json_theme_v4["color"]["frame_high"]
        self.json_theme_v5["CTkSegmentedButton"]["unselected_color"] = self.json_theme_v4["color"]["frame_low"]
        self.json_theme_v5["CTkSegmentedButton"]["unselected_hover_color"] = self.json_theme_v4["color"]["frame_border"]
        self.json_theme_v5["CTkSegmentedButton"]["text_color"] = self.json_theme_v4["color"]["text"]
        self.json_theme_v5["CTkSegmentedButton"]["text_color_disabled"] = self.json_theme_v4["color"]["text_disabled"]

        # CTkTextbox
        self.json_theme_v5["CTkTextbox"]["fg_color"] = self.json_theme_v4["color"]["entry"]
        self.json_theme_v5["CTkTextbox"]["border_color"] = self.json_theme_v4["color"]["entry_border"]
        self.json_theme_v5["CTkTextbox"]["text_color"] = self.json_theme_v4["color"]["text"]
        self.json_theme_v5["CTkTextbox"]["scrollbar_button_color"] = self.json_theme_v4["color"]["button"]
        self.json_theme_v5["CTkTextbox"]["scrollbar_button_hover_color"] = self.json_theme_v4["color"]["button_hover"]


        # CTkScrollableFrame
        self.json_theme_v5["CTkScrollableFrame"]["label_fg_color"] = self.json_theme_v4["color"]["frame_high"]

        # DropdownMenu
        self.json_theme_v5["DropdownMenu"]["fg_color"] = self.json_theme_v4["color"]["dropdown_color"]
        self.json_theme_v5["DropdownMenu"]["hover_color"] = self.json_theme_v4["color"]["dropdown_hover"]
        self.json_theme_v5["DropdownMenu"]["text_color"] = self.json_theme_v4["color"]["dropdown_text"]


    def dump_theme(self):
        try:
            with open(self.theme_file_out, "w") as f:
                json.dump(self.json_theme_v5, f, indent=2)
            print(f'Version 5 theme file, dumped to: {self.theme_file_out}.')
        except IOError:
            print(f'Failed to write file {self.theme_file_out} - possible a permissions or free space issue.')
            exit(1)


if input_theme_file == output_theme_file:
    print('ERROR: The output file pathname, cannot be the same as the input file.')
    exit(1)

if __name__ == "__main__":
    converter = ThemeConverter(application_home=app_home,
                               theme_file_in=input_theme_file,
                               theme_file_out=output_theme_file,
                               strict=retain_window_bg)
    converter.load_theme()
    converter.convert_json()
    converter.dump_theme()
