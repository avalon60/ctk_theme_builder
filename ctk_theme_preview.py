__title__ = 'CTk Theme Builder'
__author__ = 'Clive Bostock'
__version__ = "2.1.0"
__license__ = 'MIT - see LICENSE.md'

import copy
import time
import tkinter as tk
import customtkinter as ctk
from customtkinter import ThemeManager
import json
import socket
import os
import platform
import threading
from configparser import ConfigParser
from pathlib import Path
from datetime import datetime
import lib.cbtk_kit as cbtk
import lib.ctk_theme_builder_m as mod
from lib.ctk_tooltip.ctk_tooltip import CTkToolTip
from CTkMessagebox import CTkMessagebox

PROG = os.path.basename(__file__)
APP_HOME = Path(os.path.dirname(os.path.realpath(__file__)))
ASSETS_DIR = APP_HOME / 'assets'
CONFIG_DIR = ASSETS_DIR / 'config'
ETC_DIR = ASSETS_DIR / 'etc'
TEMP_DIR = APP_HOME / 'tmp'
VIEWS_DIR = ASSETS_DIR / 'views'
APP_THEMES_DIR = ASSETS_DIR / 'themes'
APP_IMAGES = ASSETS_DIR / 'images'
LISTENER_FILE = ETC_DIR / 'listener.started'
APP_DATA_DIR = ASSETS_DIR / 'data'
DB_FILE_PATH = APP_DATA_DIR / 'ctk_theme_builder.db'

DEBUG = 0
HEADER_SIZE = 64
METHOD_LISTENER_PORT = 5051
SERVER = '127.0.0.1'
METHOD_LISTENER_ADDRESS = (SERVER, METHOD_LISTENER_PORT)

ENCODING_FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
DISCONNECT_JSON = '{"command_type": "program", "command": "' + DISCONNECT_MESSAGE + '", "parameters": [""]}'

DEFAULT_VIEW = mod.DEFAULT_VIEW

listener_status = 0


def update_widget_geometry(widget, widget_property, property_value):
    if widget_property == 'corner_radius':
        widget.configure(corner_radius=property_value)
    elif widget_property == 'border_width':
        widget.configure(border_width=property_value)
    elif widget_property == 'border_width_unchecked':
        widget.deselect()
        widget.configure(border_width_unchecked=property_value)
    elif widget_property == 'border_width_checked':
        widget.select()
        widget.configure(border_width_checked=property_value)


class PreviewPanel:
    PANEL_WIDTH = 800
    PANEL_HEIGHT = 740

    def __init__(self, theme_file: str, appearance_mode: str = 'Dark'):

        self._appearance_mode = appearance_mode
        self._theme_file = theme_file
        ctk.set_default_color_theme(self._theme_file)
        ctk.set_appearance_mode(self._appearance_mode)

        self.refresh_widgets = []

        self._ASSETS_DIR = APP_HOME / 'assets'
        self._CONFIG_DIR = ASSETS_DIR / 'config'
        self._ETC_DIR = ASSETS_DIR / 'etc'
        self._VIEWS_DIR = ASSETS_DIR / 'views'
        self._palettes_dir = ASSETS_DIR / 'palettes'
        self._theme_json_dir = ASSETS_DIR / 'themes'

        # If the listener file exists, we assume someone has gone a bit
        # bonkers, hitting the 'Refresh Preview' button. Things
        # got complicated under Windows controlling this stuff, so
        # this is a bit of a basic control mechanism, to avoid having
        # to engineer a network ACK.
        if LISTENER_FILE.exists():
            exit(0)

        self._config_file = self._CONFIG_DIR / 'ctk_theme_maker.ini'

        operating_system = platform.system()
        if operating_system == "darwin":
            self._platform = "MacOS"

        if operating_system == "Windows":
            self._user_home_dir = os.getenv("UserProfile")
        else:
            self._user_home_dir = os.getenv("HOME")

        # The self._rendered_widgets property is a dictionary of widget types.
        # Under each type, we append to a list for each widget rendered. This
        # then allows us to update the rendering of colours etc, in real time
        # as changes com through.
        # TODO: Generate this dictionary, based on the default.json. This can later be leveraged, if/when new
        # TODO: widgets / properties are introduced. We also need to facilitate the filling of gaps in older versions
        # TODO: of theme JSON presented to the app.

        # self._rendered_widgets = {}
        # for widget in mod.SUPPORTED_WIDGETS:
        #    self._rendered_widgets[widget] = []

        # Initialise class properties
        self._config_file = self._CONFIG_DIR / 'ctk_theme_maker.ini'

        self._render_state = tk.NORMAL
        self._enable_tooltips = mod.preference_setting(db_file_path=DB_FILE_PATH,
                                                       scope='user_preference', preference_name='enable_tooltips')

        self._render_disabled = mod.preference_setting(db_file_path=DB_FILE_PATH,
                                                       scope='auto_save', preference_name='render_disabled')

        # self._shade_adjust_differential = int(self._config_property_val('preferences',
        #                                                                 'shade_adjust_differential', '3'))

        theme_name = os.path.basename(self._theme_file)
        self._theme_name = theme_name = os.path.splitext(theme_name)[0]

        self.preview = ctk.CTk()
        self.img_selected = cbtk.load_image(light_image=APP_IMAGES / 'colour_wheel.png', image_size=(10, 10))
        self.preview.protocol("WM_DELETE_WINDOW", self.block_closing)
        self._restore_preview_geometry()

        self.preview.columnconfigure(1, weight=1)
        self.preview.rowconfigure(0, weight=1)

        static_corner_radius = 5

        # The exec_widget_command event is generated by the _method_listener -> _handle_client methods.
        self.preview.bind("<<exec_widget_command>>", self._exec_client_command)
        self.render_preview_frames()
        # Start the command listener. This will listen for commands sent by
        # the control panel, and carry out any requested instructions.
        self.start_method_listener()
        self.preview.mainloop()

    def render_preview_frames(self):

        ipadx = 10
        ipady = 50
        # Initialise/re-initialise rendered widgets' dictionary.
        self._rendered_widgets = copy.deepcopy(mod.RENDERED_PREVIEW_WIDGETS)
        self._rendered_widgets['CTk'].append(self.preview)

        for widget in self.refresh_widgets:
            widget.destroy()

        # Get the theme being used by the control panel. We can use this to style some
        #  non-preview components in the Preview panel.
        control_panel_theme = mod.preference_setting(db_file_path=DB_FILE_PATH,
                                                     scope='user_preference', preference_name='control_panel_theme')
        control_panel_mode = mod.preference_setting(db_file_path=DB_FILE_PATH,
                                                    scope='user_preference', preference_name='control_panel_mode')
        ctl_mode_idx = cbtk.str_mode_to_int()
        self._theme_palette_buttons = {}

        control_panel_theme = control_panel_theme + '.json'
        self.control_panel_theme_path = str(self._theme_json_dir / control_panel_theme)

        self._preview_border_width = 2

        # Set the control panel frame colours we are to use. These override the
        # theme colours that we are previewing. We only want the widget preview frame to reflect the
        # colours being developed.
        self._ctl_frame_fg_color = cbtk.theme_property_color(theme_file_path=self.control_panel_theme_path,
                                                             widget_type='CTkFrame',
                                                             widget_property='fg_color',
                                                             mode=control_panel_mode)

        self._ctl_frame_top_fg_color = cbtk.theme_property_color(theme_file_path=self.control_panel_theme_path,
                                                                 widget_type='CTkFrame',
                                                                 widget_property='top_fg_color',
                                                                 mode=control_panel_mode)

        self._ctl_frame_border = cbtk.theme_property_color(theme_file_path=self.control_panel_theme_path,
                                                           widget_type='CTkFrame',
                                                           widget_property='border_color',
                                                           mode=control_panel_mode)

        self._ctl_text = cbtk.get_color_from_name(widget_type='CTkLabel',
                                                  widget_property='text_color')

        self._ctl_label = cbtk.theme_property_color(theme_file_path=self.control_panel_theme_path,
                                                    widget_type='CTkLabel',
                                                    widget_property='text_color',
                                                    mode=control_panel_mode)

        self._tooltip_fg = self._ctl_text
        self._tooltip_bg = self._ctl_frame_top_fg_color

        # This is a base frame for contrast purposes, against a top frame.
        self._frm_preview_base = ctk.CTkFrame(master=self.preview)
        self._frm_preview_base.grid(row=0, column=0, ipadx=ipadx, ipady=ipady, padx=10, pady=10, sticky='nsew')
        self._frm_preview_base.columnconfigure(0, weight=1)
        self.refresh_widgets.append(self._frm_preview_base)

        self._rendered_widgets['CTkFrame'].append(self._frm_preview_base)
        # We need a double entry. This is a bit of a cludge for dealing
        # with the top_fg_color property, which has no configure option.
        self._rendered_widgets['frame_base'].append(self._frm_preview_base)

        # This is a top frame for contrast purposes, when placed within another frame.
        self._frm_preview_top = ctk.CTkFrame(master=self._frm_preview_base)

        self._frm_preview_top.grid(row=1, column=0, ipadx=ipadx, ipady=ipady, padx=10, pady=(10, 25), sticky='nsew')
        self._rendered_widgets['CTkFrame'].append(self._frm_preview_top)
        # We need a double entry. This is a bit of a cludge for dealing
        # with the top_fg_color property, which has no configure option.
        self._rendered_widgets['frame_top'].append(self._frm_preview_top)

        self._render_frame_top_preview()

        if self._render_disabled == 1:
            self._render_preview_disabled()
        else:
            self._render_preview_enabled()

    def _switch_theme(self, theme_file: Path):
        self._theme_file = theme_file
        ctk.set_default_color_theme(self._theme_file)

        self.render_preview_frames()

    def _switch_appearance_mode(self, appearance_mode: str):
        ctk.set_default_color_theme(self._theme_file)
        self._appearance_mode = appearance_mode
        ctk.set_appearance_mode(self._appearance_mode)
        self.render_preview_frames()

    def _render_frame_top_preview(self):
        def slider_callback(value):
            self.progressbar_1.set(value)

        js = open(self._theme_file)
        json_text = json.load(js)
        colours = {}
        for item, value in json_text.items():
            if str(value).find("color") != -1:
                property = f"{item.replace('CTk', '')}/{value}"
                colours[property] = value

        widget_frame = self._frm_preview_top

        theme_name = cbtk.theme_provenence_attribute(theme_file_path=self._theme_file,
                                                     attribute="theme name",
                                                     value_on_missing='Unknown Theme Name')
        self.preview.title(f'Theme Preview [ {self._appearance_mode} / {theme_name} ]')

        pad_x = 10
        pad_y = 10

        self.lbl_preview_heading = ctk.CTkLabel(master=self._frm_preview_top,
                                                text='Frame (Top) Preview',
                                                font=mod.HEADING4,
                                                anchor="w")
        self.lbl_preview_heading.grid(row=0, column=0, pady=(10, 20))

        self._rendered_widgets['CTkLabel'].append(self.lbl_preview_heading)

        label_1 = ctk.CTkLabel(master=widget_frame, justify=tk.LEFT)
        label_1.grid(row=1, column=0, padx=pad_x, pady=pad_y)
        self._rendered_widgets['CTkLabel'].append(label_1)

        self.progressbar_1 = ctk.CTkProgressBar(master=widget_frame)
        self.progressbar_1.grid(row=2, column=0, padx=pad_x, pady=pad_y)
        self._rendered_widgets['CTkProgressBar'].append(self.progressbar_1)
        if self._enable_tooltips:
            progressbar_1tooltip = CTkToolTip(self.progressbar_1,
                                              justify="left",
                                              message='CTkProgressBar widget')

        self.slider_1 = ctk.CTkSlider(master=widget_frame, command=slider_callback, from_=0, to=1)
        self.slider_1.grid(row=3, column=0, padx=pad_x, pady=(pad_y))
        self.slider_1.set(0.5)
        if self._enable_tooltips:
            slider_1_tooltip = CTkToolTip(self.slider_1,
                                          justify="left",
                                          message='CTkSlider widget')
        self._rendered_widgets['CTkSlider'].append(self.slider_1)

        # CTkSegmentedButton
        self.seg_button = ctk.CTkSegmentedButton(master=widget_frame)
        self.seg_button.grid(row=3, column=1, padx=(25, 0), pady=pad_y, sticky="ew", columnspan=2)

        self.seg_button.configure(values=["CTkSegmentedButton", "Value 2", "Value 3"])
        self.seg_button.set("Value 2")
        self._rendered_widgets['CTkSegmentedButton'].append(self.seg_button)

        self.optionmenu_1 = ctk.CTkOptionMenu(widget_frame,
                                              # border_width=self._preview_border_width,
                                              values=["Option 1", "Option 2", "CTkOOption 42..."])
        self.optionmenu_1.grid(row=4, column=1, padx=pad_x, pady=pad_y)
        self.optionmenu_1.set("CTkOptionMenu")
        self._rendered_widgets['CTkOptionMenu'].append(self.optionmenu_1)

        self.combobox_1 = ctk.CTkComboBox(widget_frame, values=["Option 1", "Option 2", "Option 42..."])
        self.combobox_1.grid(row=5, column=1, padx=pad_x, pady=pad_y)
        self.combobox_1.set("CTkComboBox")

        self._rendered_widgets['CTkComboBox'].append(self.combobox_1)

        # CTkButton
        # We contrive to always show a contrast of a button widget with and without a border.
        button_border_width = ThemeManager.theme['CTkButton']['border_width']
        self.button_1 = ctk.CTkButton(master=widget_frame, border_width=button_border_width)
        self.button_1.grid(row=4, column=2, padx=pad_x, pady=pad_y)

        self._rendered_widgets['CTkButton'].append(self.button_1)
        if self._enable_tooltips:
            self.button_1_tooltip = CTkToolTip(self.button_1,
                                               justify="left",
                                               x_offset=-70,
                                               message=f'CTkButton - with default border setting of {button_border_width}')

        if button_border_width == 0:
            second_border_width = 2
        else:
            second_border_width = 0
        self.button_2 = ctk.CTkButton(master=widget_frame, border_width=second_border_width)
        self.button_2.grid(row=5, column=2, padx=pad_x, pady=pad_y)

        if self._enable_tooltips:
            self.button_2_tooltip = CTkToolTip(self.button_2,
                                               border_width=second_border_width,
                                               justify="left",
                                               x_offset=-70,
                                               message=f'TkButton - with border setting of {second_border_width}')

        self._rendered_widgets['CTkButton'].append(self.button_2)

        self.checkbox_1 = ctk.CTkCheckBox(master=widget_frame)
        self.checkbox_1.grid(row=1, column=2, padx=pad_x, pady=pad_y)
        self.checkbox_1.select()

        self.switch_1 = ctk.CTkSwitch(master=widget_frame)
        self.switch_1.grid(row=2, column=2, padx=pad_x, pady=pad_y)
        self.switch_1.select()
        self._rendered_widgets['CTkSwitch'].append(self.switch_1)

        self._rendered_widgets['CTkCheckBox'].append(self.checkbox_1)

        # RCTkRadioButton
        self.radiobutton_var = tk.IntVar(value=1)

        self.radiobutton_1 = ctk.CTkRadioButton(master=widget_frame, variable=self.radiobutton_var, value=1,
                                                text='CTkRadioButton')
        self.radiobutton_1.grid(row=1, column=1, padx=pad_x, pady=pad_y)

        self._rendered_widgets['CTkRadioButton'].append(self.radiobutton_1)
        self.radiobutton_1.select()

        self.radiobutton_2 = ctk.CTkRadioButton(master=widget_frame, variable=self.radiobutton_var, value=2)
        self.radiobutton_2.grid(row=2, column=1, padx=pad_x, pady=pad_y)

        self._rendered_widgets['CTkRadioButton'].append(self.radiobutton_2)

        # CTkEntry
        # We contrive to always show a contrast of an entry widget with and without a border.
        entry_border_width = ThemeManager.theme['CTkEntry']['border_width']
        if entry_border_width == 0:
            second_border_width = 2
        else:
            second_border_width = 0

        self.entry_1 = ctk.CTkEntry(master=widget_frame, placeholder_text="CTkEntry", border_width=entry_border_width)
        self.entry_1.grid(row=4, column=0, padx=pad_x, pady=pad_y)
        if self._enable_tooltips:
            self.entry_1_tooltip = CTkToolTip(self.entry_1,
                                         justify="left",
                                         wraplength=250,
                                         padding=(5, 5),
                                         message=f'CTkEntry - with default border setting of {entry_border_width}')

        self._rendered_widgets['CTkEntry'].append(self.entry_1)

        self.entry_2 = ctk.CTkEntry(master=widget_frame, border_width=second_border_width, placeholder_text="CTkEntry2")
        self.entry_2.grid(row=5, column=0, padx=pad_x, pady=pad_y)
        if self._enable_tooltips:
            self.entry_2_tooltip = CTkToolTip(self.entry_2,
                                         justify="left",
                                         wraplength=250,
                                         message=f'CTkEntry - with border setting of {second_border_width}')
        self._rendered_widgets['CTkEntry'].append(self.entry_2)

        # CTkTextbox
        self.textbox = ctk.CTkTextbox(master=widget_frame, width=250, height=250)
        self.textbox.grid(row=10, column=0, padx=(15, 0), pady=(30, 0), sticky="nsew", rowspan=1)
        if self._enable_tooltips:
            textbox_tooltip = CTkToolTip(self.textbox,
                                         wraplength=300,
                                         padding=(5, 5),
                                         x_offset=-100,
                                         justify="left",
                                         message='CTkTextbox')

        self.textbox.insert("0.0", "CTkTextbox\n\n" + "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, "
                                                      "sed diam nonumy eirmod tempor invidunt ut labore et dolore "
                                                      "magna aliquyam erat, sed diam voluptua.\n\n" * 20)

        self._rendered_widgets['CTkTextbox'].append(self.textbox)

        # CTkScrollableFrame
        self.scrollable_frame = ctk.CTkScrollableFrame(master=widget_frame,
                                                       label_text='CTkScrollableFrame',
                                                       width=160,
                                                       height=200)
        self.scrollable_frame.grid(row=10, column=1, padx=(10, 0), pady=(30, 0))
        if self._enable_tooltips:
            scrollable_frame_tooltip = CTkToolTip(self.scrollable_frame,
                                                  wraplength=300,
                                                  padding=(5, 5),
                                                  x_offset=-100,
                                                  justify="left",
                                                  message='NOTE: CTkScrollableFrame, is a composite widget. '
                                                          'With the exception of the label_fg_color, '
                                                          'theme file property, its other colour '
                                                          'properties, are defaulted from CTkFrame, '
                                                          'CTkScrollbar and CTkLabel.')

        self.scrollable_label = ctk.CTkLabel(master=self.scrollable_frame, text="Bozzy bear woz here...\n\n" * 20)
        self.scrollable_label.grid(row=0, column=0, padx=0, pady=0, sticky='ew')
        # As of CustomTkinter 5.1.2, the mousewheel bindings aren't in place for Linux.

        self._rendered_widgets['CTkScrollableFrame'].append(self.scrollable_frame)
        # CTkTabview
        self.tabview = ctk.CTkTabview(master=widget_frame, width=250)
        self.tabview.grid(row=10, column=2, padx=(20, 0), pady=(20, 10), sticky="nsew")
        self.tabview.add("CTkTabview")
        self.tabview.add("Tab 2")
        self.tabview.add("Tab 3")
        # self.tabview.tab("CTkTabview").grid_columnconfigure(0, weight=1)  # configure grid of individual tabs
        # self.tabview.tab("Tab 2").grid_columnconfigure(0, weight=1)
        self._rendered_widgets['CTkTabview'].append(self.tabview)
        self.label_tab_1 = ctk.CTkLabel(self.tabview.tab("CTkTabview"), justify='left',
                                        text="I've seen things you people\nwouldn't believe...\n\nAttack ships on fire "
                                             "off\nthe shoulder of Orion...")
        self.label_tab_1.grid(row=0, column=2, padx=20, pady=20)
        self.label_tab_2 = ctk.CTkLabel(self.tabview.tab("Tab 2"), justify='left',
                                        text="I watched C-beams glitter in\nthe dark near the Tannhäuser\nGate.")
        self.label_tab_2.grid(row=0, column=0, padx=20, pady=20)
        self.label_tab_3 = ctk.CTkLabel(self.tabview.tab("Tab 3"), justify='left',
                                        text="All those moments will be\nlost in time, like tears\nin rain...\n\n\n"
                                             "Time to die.")
        self.label_tab_3.grid(row=0, column=0, padx=20, pady=20, sticky='nsew')
        if self._enable_tooltips:
            label_tab_1_tooltip = CTkToolTip(self.label_tab_1,
                                             justify="left",
                                             wraplength=250,
                                             x_offset=-120,
                                             padding=(5, 5),
                                             message='The CTkTabview is a composite widget. As of CustomTkinter 5.1.2, '
                                                     'it has no direct default properties. instead it borrows from '
                                                     'CTkFrame and CTkSegmentedButton.')
            label_tab_2_tooltip = CTkToolTip(self.label_tab_2,
                                             justify="left",
                                             wraplength=250,
                                             x_offset=-120,
                                             padding=(5, 5),
                                             message='The CTkTabview is a composite widget. As of CustomTkinter 5.1.2, '
                                                     'it has no direct default properties. instead it borrows from '
                                                     'CTkFrame and CTkSegmentedButton.')
            label_tab_3_tooltip = CTkToolTip(self.label_tab_3,
                                             justify="left",
                                             wraplength=250,
                                             x_offset=-120,
                                             padding=(5, 5),
                                             message='The CTkTabview is a composite widget. As of CustomTkinter 5.1.2, '
                                                     'it has no direct default properties. instead it borrows from '
                                                     'CTkFrame and CTkSegmentedButton.')

    def _render_preview_disabled(self):
        self._toggle_preview_disabled(render_state=tk.DISABLED)

    def _render_preview_enabled(self):
        self._toggle_preview_disabled(render_state=tk.NORMAL)

    def render_base_frame(self):
        self.lbl_preview_heading.configure(text='Frame (Base) Preview')
        self._frm_preview_top.configure(fg_color="transparent", border_width=0)

    def render_top_frame(self):
        self.lbl_preview_heading.configure(text='Frame (Top) Preview')
        self._ctl_frame_top_fg_color = cbtk.theme_property_color(theme_file_path=self._theme_file,
                                                                 widget_type='CTkFrame',
                                                                 widget_property='top_fg_color',
                                                                 mode=self._appearance_mode)
        border_width = cbtk.theme_property(theme_file_path=self._theme_file,
                                           widget_type='CTkFrame',
                                           widget_property='border_width')
        self._frm_preview_top.configure(fg_color=self._ctl_frame_top_fg_color, border_width=border_width)

    def _toggle_preview_disabled(self, render_state):
        """Toggle between the normal and disabled states for the previewed widgets. Here we take advantage of the
        established self._rendered_widgets list, to determine the widgets which need updating."""

        for entry in self._rendered_widgets['CTkButton']:
            entry.configure(state=render_state)

        for entry in self._rendered_widgets['CTkCheckBox']:
            entry.configure(state=render_state)

        for entry in self._rendered_widgets['CTkComboBox']:
            entry.configure(state=render_state)

        for entry in self._rendered_widgets['CTkDropdownMenu']:
            entry.configure(state=render_state)

        for entry in self._rendered_widgets['CTk']:
            entry.configure(state=render_state)

        for entry in self._rendered_widgets['CTkEntry']:
            entry.configure(state=render_state)

        for entry in self._rendered_widgets['CTkLabel']:
            entry.configure(state=render_state)

        for entry in self._rendered_widgets['CTkOptionMenu']:
            entry.configure(state=render_state)

        # for entry in self._rendered_widgets['CTkProgressBar']:
        #    entry.configure(state=render_state)

        for entry in self._rendered_widgets['CTkRadioButton']:
            entry.configure(state=render_state)

        for entry in self._rendered_widgets['CTkSegmentedButton']:
            entry.configure(state=render_state)

        for entry in self._rendered_widgets['CTkSlider']:
            entry.configure(state=render_state)

        for entry in self._rendered_widgets['CTkSwitch']:
            entry.configure(state=render_state)

        for entry in self._rendered_widgets['CTkTextbox']:
            entry.configure(state=render_state)

        # TODO: Widgets missing from above list
        if render_state == tk.NORMAL:
            enable = 0
        else:
            enable = 1
        self._render_disabled = enable

    def block_closing(self, event=0):
        pass

    def _restore_preview_geometry(self):
        panel_geometry = mod.preference_setting(db_file_path=DB_FILE_PATH,
                                                scope='window_geometry',
                                                preference_name='preview_panel')
        self.preview.geometry(panel_geometry)
        self.preview.resizable(True, True)

    def _save_preview_geometry(self):
        # save current geometry to the preferences
        geometry_row = mod.preference_row(db_file_path=DB_FILE_PATH,
                                          scope='window_geometry',
                                          preference_name='preview_panel')
        panel_geometry = self.preview.geometry()
        geometry_row["preference_value"] = panel_geometry
        mod.upsert_preference(db_file_path=DB_FILE_PATH, preference_row_dict=geometry_row)

    def exec_program_command(self):

        command_json = self._command_json
        command = command_json['command']
        if command == 'quit':
            self._save_preview_geometry()
            print('Preview panel quitting...')
            if LISTENER_FILE.exists():
                os.remove(LISTENER_FILE)
            exit(0)
        if command == 'refresh':
            ctk.set_default_color_theme(self._theme_file)
            ctk.set_appearance_mode(self._appearance_mode)
            # So we need to call the render preview frames method. This
            # will destroy and rebuild the widgets.
            self.render_preview_frames()
            return

        parameters = command_json['parameters']
        # print(f'Command: {command} / Parameters: {parameters}')
        if command == 'set_appearance_mode':
            mode = parameters[0]
            self._appearance_mode = mode
            self._switch_appearance_mode(appearance_mode=mode)
        elif command == 'render_preview_disabled':
            self._render_preview_disabled()
        elif command == 'render_preview_enabled':
            self._render_preview_enabled()
        elif command == 'render_top_frame':
            self.render_top_frame()
        elif command == 'render_base_frame':
            self.render_base_frame()

    def _exec_colour_command(self):
        command_json = self._command_json
        command = command_json['command']
        if command == 'update_widget_colour':
            parameters = command_json['parameters']
            widget_type = parameters[0]
            widget_property = parameters[1]
            widget_colour = parameters[2]
            # print(f'Updating widget {widget_type} / {widget_property}')
            self._update_widget_colour(widget_type, widget_property, widget_colour)
        else:
            print(f'ERROR: Unrecognised method request: {command}')

    def _exec_geometry_command(self):
        """This method is responsible for updating widget geometry, based on commands JSON received from the
        Control Panel."""
        command_json = self._command_json
        command = command_json['command']
        if command != 'update_widget_geometry':
            print(f'ERROR: Unrecognised method request: {command}')
            return

        parameters = command_json['parameters']
        widget_type = parameters[0]
        widget_property = parameters[1]
        property_value = parameters[2]

        if widget_type == 'CTkFrame':
            for widget in self._rendered_widgets['frame_base']:
                update_widget_geometry(widget, widget_property, int(property_value))
            for widget in self._rendered_widgets['frame_top']:
                update_widget_geometry(widget, widget_property, int(property_value))
            if widget_property in ("corner_radius", "border_width"):
                for widget in self._rendered_widgets['CTkScrollableFrame']:
                    update_widget_geometry(widget, widget_property, int(property_value))
                for widget in self._rendered_widgets['CTkTabview']:
                    update_widget_geometry(widget, widget_property, int(property_value))

        else:
            for widget in self._rendered_widgets[widget_type]:
                json_widget_type = mod.json_widget_type(widget_type=widget)
                update_widget_geometry(widget, widget_property, int(property_value))

        # We contrive to always show a contrast of a button with and without a border.
        if widget_type == 'CTkButton' and widget_property == 'border_width':
            button_border_width = int(property_value)
            self.button_1.configure(border_width=button_border_width)

            if self._enable_tooltips:
                self.button_1_tooltip.configure(message=f'CTkButton - with default border setting of '
                                                        f'{button_border_width}')

            if button_border_width == 0:
                second_border_width = 2
            else:
                second_border_width = 0

            self.button_2.configure(border_width=second_border_width)

            if self._enable_tooltips:
                self.button_2_tooltip.configure(message=f'TkButton - with border setting of {second_border_width}')

        elif widget_type == 'CTkEntry' and widget_property == 'border_width':

            # We contrive to always show a contrast of an entry widget with and without a border.
            entry_border_width = int(property_value)
            self.entry_1.configure(border_width=entry_border_width)

            if self._enable_tooltips:
                self.entry_1_tooltip.configure(message=f'CTkEntry - with default border setting of '
                                                       f'{entry_border_width}')

            if entry_border_width == 0:
                second_border_width = 2
            else:
                second_border_width = 0

            self.entry_2.configure(border_width=second_border_width)
            if self._enable_tooltips:
                self.entry_2_tooltip.configure(message=f'CTkEntry - with border setting of {second_border_width}')

    def _exec_client_command(self, evt):
        command_json = self._command_json
        command_type = command_json['command_type']

        if command_type == 'program':
            self.exec_program_command()
        # print('Calling exec_program_command')
        elif command_type == 'colour':
            # print('Calling exec_colour_command')
            self._exec_colour_command()
        elif command_type == 'geometry':
            # print('Calling exec_geometry_command')
            self._exec_geometry_command()

    def _handle_client(self, conn, address: str):
        """Here, handle client, expects a header frame, followed by a command frame.
        The header frame tells us how long the content of the subsequent command
        frame is. We then unpack the command frame and pass the contents to be
        processed, by the process_client_command function."""
        # print(f'[ NEW_CONNECTION ] {address} connected')
        connected = True

        while connected:
            header_frame = conn.recv(HEADER_SIZE).decode(ENCODING_FORMAT)
            # print(f'[ HEADER_FRAME ] <{header_frame}>')
            if header_frame:
                msg_length = int(header_frame)
                command_json_str = conn.recv(msg_length).decode(ENCODING_FORMAT)
                command_json = json.loads(command_json_str)
                # print(command_json)
                command_type = command_json['command_type']
                command = command_json['command']

                if command == DISCONNECT_MESSAGE and command_type == 'program':
                    if DEBUG:
                        print(f'[{address}] Session disconnected')
                    del self._client_handlers[conn]
                    connected = False
                else:
                    self._command_json = command_json
                    self.preview.event_generate('<<exec_widget_command>>', when='tail')

        conn.close()
        return

    def _method_listener(self):
        """Initialise our listener's client_handlers dictionary. This will keep track of connected
        sessions (there should normally be only one). Each incoming request, is handed off to the
        handle_client function.
        """
        global listener_status
        self._client_handlers = {}
        print("Method listener starting...")
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server.bind(METHOD_LISTENER_ADDRESS)
        except OSError:
            print(f'Preview Panel, socket bind error. ensure that no other instances of CTk Theme Builder are running '
                  f'and that port 5051 is free.')
            listener_status = -1
            raise
        server.listen()
        # current dateTime
        now = datetime.now()
        # convert to string
        date_started = now.strftime("%b %d %Y %H:%M:%S")
        print('PREVIEW: Checking for listener file...')
        if not LISTENER_FILE.exists():
            print('PREVIEW: Listener file missing, creating...')
            with open(LISTENER_FILE, 'w') as f:
                pid = os.getpid()
                f.write(f'[{pid}] CTk Theme Builder listener started at: {date_started}')
        print(f'Method listener started on port: {METHOD_LISTENER_PORT}')
        while True:
            # print('Waiting for a client request...')
            conn, address = server.accept()
            client_thread = threading.Thread(target=self._handle_client,
                                             args=(conn, address),
                                             daemon=True)
            client_thread.start()
            self._client_handlers[conn] = client_thread
            # print(f'Client handlers: {self._client_handlers[conn]}')
            # Here we subtract two from the thread count. We don't count the listener or the main thread as clients.
            # print(f'[ ACTIVE CONNECTIONS ] {threading.active_count() - 2}')

    @staticmethod
    def _prepare_message(message):

        message = message.encode(ENCODING_FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(ENCODING_FORMAT)
        send_length += b' ' * (HEADER_SIZE - len(send_length))
        return send_length, message

    def start_method_listener(self):
        listener_thread = threading.Thread(target=self._method_listener, daemon=True)
        listener_thread.start()
        # Give the listener time to attempt to attach to the socket,
        # and report if it has a problem.
        time.sleep(0.1)
        if listener_status == -1:
            confirm = CTkMessagebox(
                title='Socket Error',
                message=f'The listener failed to bind to port {METHOD_LISTENER_PORT}\n\n'
                        f'Ensure that only one instance of {__title__} is running and that no '
                        f'other process is using the port.',
                option_1='OK')
            if confirm.get() == 'OK':
                exit(1)

    def _update_widget_colour(self, widget_type, widget_property, widget_colour):
        print(f'_update_widget_colour: widget_type: {widget_type}; widget_property: {widget_property}')
        # We lowercase the widget property, due to an issue in CustomTkinter 5.1.2, where there was an fg_Color
        # property against CTkSwitch. This was fixed to fg_color in 5.1.3.
        widget_property_lower = widget_property.lower()

        if widget_type == 'CTkFrame' and widget_property_lower == 'top_fg_color':
            widget_type = 'frame_top'
            widget_property_lower = 'fg_color'
        elif widget_type == 'CTkFrame' and widget_property_lower == 'fg_color':
            widget_type = 'frame_base'

        for widget in self._rendered_widgets[widget_type]:
            print(f'Updating {widget_property_lower} for widget of type "{widget_type}"')
            if widget_property_lower == 'border_color':
                widget.configure(border_color=widget_colour)
            elif widget_property_lower == 'button_color':
                widget.configure(button_color=widget_colour)
            elif widget_property_lower == 'button_hover_color':
                widget.configure(button_hover_color=widget_colour)
            elif widget_property_lower == 'checkmark_color':
                widget.configure(checkmark_color=widget_colour)
            elif widget_property_lower == 'fg_color':
                widget.configure(fg_color=widget_colour)
            elif widget_property_lower == 'hover_color':
                widget.configure(hover_color=widget_colour)
            elif widget_property_lower == 'label_fg_color':
                widget.configure(label_fg_color=widget_colour)
            elif widget_property_lower == 'placeholder_text_color':
                widget.configure(placeholder_text_color=widget_colour)
            elif widget_property_lower == 'progress_color':
                widget.configure(progress_color=widget_colour)
            elif widget_property_lower == 'scrollbar_button_color':
                widget.configure(scrollbar_button_color=widget_colour)
            elif widget_property_lower == 'scrollbar_button_hover_color':
                widget.configure(scrollbar_button_hover_color=widget_colour)
            elif widget_property_lower == 'selected_color':
                widget.configure(selected_color=widget_colour)
            elif widget_property_lower == 'selected_hover_color':
                widget.configure(selected_hover_color=widget_colour)
            elif widget_property_lower == 'text_color':
                widget.configure(text_color=widget_colour)
            elif widget_property_lower == 'text_color_disabled':
                widget.configure(text_color_disabled=widget_colour)
            elif widget_property_lower == 'unselected_color':
                widget.configure(unselected_color=widget_colour)
            elif widget_property_lower == 'unselected_hover_color':
                widget.configure(unselected_hover_color=widget_colour)
            else:
                print(f'WARNING: Unrecognised widget property: {widget_property_lower}')
        # Now deal with composite widgets, which share properties with other widget types.
        # Scrollable Frames
        if widget_type == 'frame_base':
            print(self._rendered_widgets)
            for widget in self._rendered_widgets['CTkScrollableFrame']:
                if widget_property_lower == 'fg_color':
                    widget.configure(fg_color=widget_colour)
                elif widget_property_lower == 'border_color':
                    widget.configure(border_color=widget_colour)
            for widget in self._rendered_widgets['CTkTabview']:
                if widget_property_lower == 'fg_color':
                    widget.configure(fg_color=widget_colour)
                elif widget_property_lower == 'border_color':
                    widget.configure(border_color=widget_colour)

        elif widget_type == 'CTkScrollbar' and widget_property_lower in ('fg_color', 'button_color',
                                                                         'button_hover_color'):
            for widget in self._rendered_widgets['CTkScrollableFrame']:
                if widget_property_lower == 'fg_color':
                    widget.configure(scrollbar_fg_color=widget_colour)
                elif widget_property_lower == 'button_color':
                    widget.configure(scrollbar_button_color=widget_colour)
                elif widget_property_lower == 'button_hover_color':
                    widget.configure(scrollbar_button_hover_color=widget_colour)
        elif widget_type == 'CTkLabel' and widget_property_lower in ('fg_color', 'text_color'):
            # TODO: print('Updating CTkScrollableFrame objects...')
            for widget in self._rendered_widgets['CTkScrollableFrame']:
                if widget_property_lower == 'fg_color':
                    widget.configure(label_fg_color=widget_colour)
                elif widget_property_lower == 'text_color':
                    widget.configure(label_text_color=widget_colour)
        elif widget_type == 'CTkFrame' and widget_property_lower:
            for widget in self._rendered_widgets['CTkTabview']:
                if widget_property_lower == 'fg_color':
                    widget.configure(fg_color=widget_colour)
        elif widget_type == 'CTkSegmentedButton' and widget_property_lower:
            for widget in self._rendered_widgets['CTkTabview']:
                if widget_property_lower == 'fg_color':
                    widget.configure(segmented_button_fg_color=widget_colour)
                elif widget_property_lower == 'selected_color':
                    widget.configure(segmented_button_selected_color=widget_colour)
                elif widget_property_lower == 'selected_hover_color':
                    widget.configure(segmented_button_unselected_hover_color=widget_colour)
                elif widget_property_lower == 'unselected_hover_color':
                    widget.configure(segmented_button_unselected_hover_color=widget_colour)
                elif widget_property_lower == 'unselected_color':
                    widget.configure(segmented_button_unselected_color=widget_colour)
                elif widget_property_lower == 'text_color':
                    widget.configure(text_color=widget_colour)
                elif widget_property_lower == 'text_color_disabled':
                    widget.configure(text_color_disabled=widget_colour)


if __name__ == "__main__":
    pass
