__title__ = 'CTk Theme Builder'
__author__ = 'Clive Bostock'
__version__ = "2.1.0"
__license__ = 'MIT - see LICENSE.md'

import configparser
import copy

# A hat tip and thankyou, to Tom Schimansky for is excellent CustomTkinter.
# Credit to my friend and colleague Jan Bejec, as well as my wife for their contributions to my logo.
# Also a thankyou to Akash Bora for producing the CTkToolTip and CTkMessagebox widgets.

import argparse
import tkinter as tk
import customtkinter as ctk

from configparser import ConfigParser
import json
import subprocess as sp
from argparse import HelpFormatter
import socket
from operator import attrgetter
import os
import operator
import platform
import pyperclip
import re
import shutil
from tkinter import filedialog
from tkinter.colorchooser import askcolor
from pathlib import Path
import time
from datetime import datetime
import colorharmonies as ch
from enum import Enum
import lib.cbtk_kit as cbtk
from ctk_theme_preview import PreviewPanel
from ctk_theme_preview import update_widget_geometry
import ctk_theme_preview
import lib.ctk_theme_builder_m as mod
from lib.ctk_tooltip.ctk_tooltip import CTkToolTip
from CTkMessagebox import CTkMessagebox

# import lib.CTkMessagebox.ctkmessagebox

HEADING1 = mod.HEADING1
HEADING2 = mod.HEADING2
HEADING3 = mod.HEADING3
HEADING4 = mod.HEADING4
REGULAR_TEXT = cbtk.REGULAR_TEXT
SMALL_TEXT = cbtk.SMALL_TEXT

DEBUG = 0
HEADER_SIZE = ctk_theme_preview.HEADER_SIZE
SERVER = ctk_theme_preview.SERVER
METHOD_LISTENER_ADDRESS = ctk_theme_preview.METHOD_LISTENER_ADDRESS
ENCODING_FORMAT = ctk_theme_preview.ENCODING_FORMAT
DISCONNECT_MESSAGE = ctk_theme_preview.DISCONNECT_MESSAGE
DISCONNECT_JSON = ctk_theme_preview.DISCONNECT_JSON

LISTENER_FILE = ctk_theme_preview.LISTENER_FILE

DEFAULT_VIEW = mod.DEFAULT_VIEW
preview_panel = None

PROG = os.path.basename(__file__)
APP_HOME = Path(os.path.dirname(os.path.realpath(__file__)))

CTK_SITE_PACKAGES = Path(ctk.__file__)
CTK_SITE_PACKAGES = os.path.dirname(CTK_SITE_PACKAGES)
CTK_ASSETS = CTK_SITE_PACKAGES / Path('assets')
CTK_THEMES = CTK_ASSETS / 'themes'

ASSETS_DIR = APP_HOME / 'assets'
CONFIG_DIR = ASSETS_DIR / 'config'
ETC_DIR = ASSETS_DIR / 'etc'
TEMP_DIR = APP_HOME / 'tmp'
VIEWS_DIR = ASSETS_DIR / 'views'
APP_THEMES_DIR = ASSETS_DIR / 'themes'
APP_DATA_DIR = ASSETS_DIR / 'data'
APP_IMAGES = ASSETS_DIR / 'images'
DB_FILE_PATH = APP_DATA_DIR / 'ctk_theme_builder.db'

# Grab the JSON for the default view.
default_view_file = VIEWS_DIR / f'{DEFAULT_VIEW}.json'
DEFAULT_VIEW_WIDGET_ATTRIBUTES = mod.json_dict(json_file_path=default_view_file)


def valid_theme_name(theme_name):
    pattern = re.compile("[A-Za-z0-9_()]+")
    if pattern.fullmatch(theme_name):
        return True
    else:
        return False


# TODO - move to cbtk_kit


def hex_to_rgb(hex_colour):
    """ Convert a hex colour code to an RGB tuple."""
    rgb = []
    hex_value = hex_colour.replace('#', '')
    for i in (0, 2, 4):
        decimal = int(hex_value[i:i + 2], 16)
        rgb.append(decimal)

    return tuple(rgb)


def rgb_to_hex(rgb: tuple):
    """Convert RGB tuple to a hex colour code."""
    r, g, b = rgb
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)


def all_widget_attributes(widget_attributes):
    """This function receives a dictionary, based on JSON theme builder view file content,
    and scans it, to build a list of all the widget properties included in the view."""
    all_attributes = []
    for value_list in widget_attributes.values():
        all_attributes = all_attributes + value_list
    return all_attributes


def all_widget_categories(widget_attributes):
    """This function receives a dictionary, based on JSON theme builder view file content,
    and scans it, to build a list of all the widget categories included in the view. The categories
    are the select options we see, in the Filter View drop-down list, once we have selected a Properties View."""
    categories = []
    for category in widget_attributes:
        categories.append(category)
    categories.sort()
    return categories


# Add a category of All to the DEFAULT_VIEW_WIDGET_ATTRIBUTES already defined.
# This lists every widget property under the one key.
DEFAULT_VIEW_WIDGET_ATTRIBUTES['All'] = all_widget_attributes(DEFAULT_VIEW_WIDGET_ATTRIBUTES)


def run_preview_panel(appearance_mode, theme_file):
    """ Function to launch the preview panel."""
    global preview_panel
    preview_panel = PreviewPanel(appearance_mode=appearance_mode, theme_file=theme_file)


class SortingHelpFormatter(HelpFormatter):
    def add_arguments(self, actions):
        actions = sorted(actions, key=attrgetter('option_strings'))
        super(SortingHelpFormatter, self).add_arguments(actions)


class ControlPanel:
    _theme_json_dir: Path
    PANEL_HEIGHT = 905
    PANEL_WIDTH = 1020
    THEME_PALETTE_TILES = 16
    THEME_PALETTE_TILE_WIDTH = 8
    THEME_PALETTE_ROWS = 2

    # We normally list entries here, where the configure method has a bug or is subject to an omission.
    # Issue numbers and descriptions:
    #   CTk 5.1.2 CTkCheckBox.configure(text_color_disabled=...) causes exception #1591
    #   CTk 5.1.2: Omission: Theme JSON property checkmark_color of CTkCheckBox has no configure option #1586
    #   CTk 5.1.2: CTkSegmentedButton property setting issues #1562
    #   CTk 5.1.2: CTkOptionMenu.configure(text_color_disabled=...) raises exception #1559
    # The DropdownMenu is a different case. This is not a widget in its own right and so has no methods to
    # update the widgets which utilise it. E.g. CTkComboBox, CTkOptionMenu.
    # In any case, any entries in the list, require a full preview panel refresh, to work around the respective
    # challenges.
    FORCE_REFRESH_PROPERTIES = ["DropdownMenu: fg_color",
                                "DropdownMenu: hover_color",
                                "DropdownMenu: text_color",
                                "Frame: top_fg_color",
                                "CheckBox: text_color_disabled",
                                "Scrollbar: button_color",
                                "Scrollbar: button_hover_color",
                                "OptionMenu: text_color_disabled",
                                "Switch: text_color_disabled"
                                ]

    def __init__(self):
        # Grab the JSON for one of the JSON files released with the
        # installed instance of CustomTkinter
        self.theme_json_data = {}
        print('DEBUG - started')
        green_theme_file = CTK_THEMES / 'green.json'
        with open(green_theme_file) as json_file:
            self.reference_theme_json = json.load(json_file)

        self.theme = None
        self.ASSETS_DIR = APP_HOME / 'assets'
        self.log_dir = APP_HOME / 'logs'
        self.CONFIG_DIR = ASSETS_DIR / 'config'
        self.ETC_DIR = ASSETS_DIR / 'etc'
        self.VIEWS_DIR = ASSETS_DIR / 'views'
        self.palettes_dir = ASSETS_DIR / 'palettes'

        self.ctk_control_panel = ctk.CTk()
        this_platform = platform.system()
        if this_platform == "Darwin":
            self.platform = "MacOS"

        self.new_theme_json_dir = None

        if this_platform == "Windows":
            self.user_home_dir = os.getenv("UserProfile")
            self.user_name = os.getenv("LOGNAME")
        else:
            self.user_name = os.getenv("USER")
            self.user_home_dir = os.getenv("HOME")

        if LISTENER_FILE.exists():
            try:
                os.remove(LISTENER_FILE)
            except PermissionError:
                print(f'ERROR: Could not remove listener semaphore file, {LISTENER_FILE}.')
                print(f'Only one instance of {PROG}, should be running.')
                exit(0)

        # Initialise class properties
        self.user_home_dir = Path(self.user_home_dir)
        self.process = None
        self.ctk_control_panel.protocol("WM_DELETE_WINDOW", self.close_panels)
        self.json_state = 'clean'
        self.widgets = {}
        self.rendered_harmony_buttons = []
        self.rendered_harmony_labels = []
        self.rendered_keystone_shades = []
        self.harmony_palette_running = False
        self.keystone_colour = None
        self.client_socket = None

        self.properties_view = 'All'
        self.widget_attributes = DEFAULT_VIEW_WIDGET_ATTRIBUTES

        # If this is the first time the app is run, create an app home directory.
        if not self.CONFIG_DIR.exists():
            print(f'Initialising application: {self.CONFIG_DIR}')
            os.mkdir(self.CONFIG_DIR)

        self.enable_tooltips = mod.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                      preference_name='enable_tooltips')

        self.enable_palette_labels = mod.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                            preference_name='enable_palette_labels')

        self.enable_single_click_paste = mod.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                                preference_name='enable_single_click_paste')

        self.theme_json_dir = mod.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                     preference_name='theme_json_dir')

        self.last_theme_on_start = mod.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                          preference_name='last_theme_on_start')

        if self.last_theme_on_start == 'NO_DATA_FOUND':
            self.last_theme_on_start = mod.new_preference_dict(scope='user_preference',
                                                               preference_name='last_theme_on_start',
                                                               data_type='int', preference_value=0)
            mod.upsert_preference(db_file_path=DB_FILE_PATH, preference_row_dict=self.last_theme_on_start)
        if not self.theme_json_dir.exists():
            self.theme_json_dir = APP_HOME / 'user_themes'

        self.shade_adjust_differential = mod.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                                preference_name='shade_adjust_differential')

        self.harmony_contrast_differential = mod.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                                    preference_name='harmony_contrast_differential')

        self.render_disabled = mod.preference_setting(db_file_path=DB_FILE_PATH, scope='auto_save',
                                                      preference_name='render_disabled')

        self.theme_author = mod.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                   preference_name='theme_author')

        self.min_ctk_version = mod.preference_setting(db_file_path=DB_FILE_PATH, scope='system',
                                                      preference_name='min_ctk_version')

        base_ctk_version = ctk.__version__
        base_ctk_version = base_ctk_version[:base_ctk_version.index('.')]

        base_min_version = self.min_ctk_version
        base_min_version = base_min_version[:base_min_version.index('.')]

        control_panel_theme = mod.preference_setting(db_file_path=DB_FILE_PATH,
                                                     scope='user_preference', preference_name='control_panel_theme')

        control_panel_theme = control_panel_theme + '.json'

        self.control_panel_theme = str(APP_THEMES_DIR / control_panel_theme)
        # The control_panel_mode holds the  CustomTkinter appearance mode (Dark / Light)

        self.control_panel_mode = mod.preference_setting(db_file_path=DB_FILE_PATH,
                                                         scope='user_preference', preference_name='control_panel_mode')
        self.TEMP_DIR = TEMP_DIR

        ctl_mode_idx = cbtk.str_mode_to_int(self.control_panel_mode)
        control_panel_theme_path = str(APP_THEMES_DIR / control_panel_theme)

        # Some widgets we use, by necessity, are not CustomTkinter widgets. We need to colour these
        # based on the control panel's theme.
        self.ctl_frame_high = cbtk.theme_property_color(theme_file_path=control_panel_theme_path,
                                                        widget_type="CTkToplevel",
                                                        widget_property='fg_color',
                                                        mode=self.control_panel_mode
                                                        )

        self.ctl_text = cbtk.theme_property_color(theme_file_path=control_panel_theme_path,
                                                  widget_type="CTkLabel",
                                                  widget_property="text_color",
                                                  mode=self.control_panel_mode
                                                  )

        self.ctl_frame_border = cbtk.theme_property_color(theme_file_path=control_panel_theme_path,
                                                          widget_type="CTkFrame",
                                                          widget_property='fg_color',
                                                          mode=self.control_panel_mode
                                                          )

        try:
            ctk.set_default_color_theme(self.control_panel_theme)
        except FileNotFoundError:
            ctk.set_default_color_theme('blue')
            print(f'Preferred Control Panel, theme file not found. Falling back to "blue" theme.')
        ctk.set_appearance_mode(self.control_panel_mode)

        self.restore_controller_geometry()

        self.ctk_control_panel.rowconfigure(3, weight=1)
        self.ctk_control_panel.columnconfigure(0, weight=1)

        self.ctk_control_panel.title('CTk Theme Builder')

        # Instantiate Frames
        title_frame = ctk.CTkFrame(master=self.ctk_control_panel)
        title_frame.pack(fill="both", expand=0)

        self.frm_control = ctk.CTkFrame(master=self.ctk_control_panel)
        self.frm_control.columnconfigure(1, weight=1)
        self.frm_control.pack(fill="both", expand=1)
        self.frm_control.rowconfigure(2, weight=1)
        self.frm_button = ctk.CTkFrame(master=self.frm_control)
        self.frm_geometry = ctk.CTkFrame(master=self.frm_control)
        self.frm_theme_palette = ctk.CTkFrame(master=self.frm_control)
        self.frm_colour_edit_widgets = ctk.CTkScrollableFrame(master=self.frm_control)

        button_frame = self.frm_button
        button_frame.grid(row=0, column=0, rowspan=3, columnspan=1, sticky='ns', padx=(5, 5), pady=(5, 5))

        self.frm_geometry.grid(row=0, column=1, rowspan=1, sticky='nswe', padx=(0, 5), pady=(5, 5))
        self.frm_theme_palette.grid(row=1, column=1, rowspan=1, sticky='nswe', padx=(0, 5), pady=(5, 5))
        self.frm_colour_edit_widgets.grid(row=2, column=1, rowspan=1, sticky='nswe', padx=(0, 5), pady=(5, 5))
        self.status_bar = cbtk.CBtkStatusBar(master=self.ctk_control_panel,
                                             status_text_life=30,
                                             use_grid=False)
        self.ctk_control_panel.bind("<Configure>", self.status_bar.auto_size_status_bar)

        # Populate Frames
        self.lbl_title = ctk.CTkLabel(master=title_frame, text='Control Panel', font=HEADING4, anchor='w')
        self.lbl_title.grid(row=0, column=0, columnspan=2, sticky='w', padx=10, pady=5)
        master = title_frame.columnconfigure(0, weight=1)

        self.lbl_theme = ctk.CTkLabel(master=self.frm_button, text='Select Theme:')
        self.lbl_theme.grid(row=1, column=0, sticky='w', pady=(10, 0), padx=(15, 10))

        self.json_files = self.user_themes_list()
        initial_display = self.user_themes_list()
        last_theme = mod.preference_setting(db_file_path=DB_FILE_PATH, scope='auto_save',
                                            preference_name='selected_theme')
        #
        if self.last_theme_on_start:
            initial_display.insert(0, last_theme)
        else:
            initial_display.insert(0, '-- Select Theme --')
        self.opm_theme = ctk.CTkOptionMenu(master=self.frm_button,
                                           values=initial_display,
                                           command=self.load_theme)
        self.opm_theme.grid(row=3, column=0)

        self.lbl_mode = ctk.CTkLabel(master=self.frm_button, text='Preview Appearance:')
        self.lbl_mode.grid(row=5, column=0, sticky='w', pady=(10, 0), padx=(15, 10))

        mode = mod.preference_setting(db_file_path=DB_FILE_PATH, scope='auto_save',
                                      preference_name='appearance_mode')
        self.tk_seg_mode = ctk.StringVar(value=mode + ' Mode')
        self.seg_mode = ctk.CTkSegmentedButton(self.frm_button,
                                               values=['Light Mode', 'Dark Mode'],
                                               width=30,
                                               border_width=1,
                                               command=self.switch_preview_appearance_mode,
                                               variable=self.tk_seg_mode)
        self.seg_mode.grid(row=6, column=0, padx=10, sticky='w')

        self.tk_swt_frame_mode = ctk.StringVar(value="top")
        self.swt_frame_mode = ctk.CTkSwitch(self.frm_button,
                                            state=tk.DISABLED,
                                            text='Top Frame',
                                            onvalue="top", offvalue="base",
                                            command=self.toggle_frame_mode,
                                            variable=self.tk_swt_frame_mode)
        self.swt_frame_mode.grid(row=7, column=0, padx=18, pady=(20, 0), sticky='w')

        if self.enable_tooltips:
            frame_mode_tooltip = CTkToolTip(self.swt_frame_mode,
                                            wraplength=400,
                                            justify="left",
                                            message='When enabled, the Preview Panel appears as a Top Frame render. '
                                                    '\n\n'
                                                    'When configuring a frame, stacked on top of another frame, the '
                                                    'top frame is rendered using the top_fg_color property. In all '
                                                    'likelihood, you will want to observe how your other widget '
                                                    'property colours render as a base frame, as well as a top frame.')

        self.tk_render_disabled = tk.IntVar(master=self.frm_button, value=self.render_disabled)
        self.swt_render_disabled = ctk.CTkSwitch(master=self.frm_button,
                                                 text='Render Disabled',
                                                 variable=self.tk_render_disabled,
                                                 state=tk.DISABLED,
                                                 command=self.toggle_render_disabled)
        self.swt_render_disabled.grid(row=8, column=0, padx=10, pady=(10, 0))

        self.lbl_widget_view = ctk.CTkLabel(master=self.frm_button,
                                            text='Properties View:')
        self.lbl_widget_view.grid(row=9, column=0, sticky='w', pady=(20, 0), padx=(15, 10))

        self.widget_categories = all_widget_categories(DEFAULT_VIEW_WIDGET_ATTRIBUTES)
        self.views_list = self.view_list()
        self.tk_widget_view = tk.StringVar(value=DEFAULT_VIEW)
        self.opm_properties_view = ctk.CTkOptionMenu(master=self.frm_button,
                                                     command=self.update_properties_filter,
                                                     variable=self.tk_widget_view,
                                                     values=self.views_list,
                                                     state=tk.DISABLED)
        self.opm_properties_view.grid(row=10, column=0)
        if self.enable_tooltips:
            filter_view_tooltip = CTkToolTip(self.opm_properties_view,
                                             wraplength=400,
                                             justify="left",
                                             message='Views help you to target specific widgets, or groups of  '
                                                     'related widgets, and their associated properties. ')

        self.lbl_filter = ctk.CTkLabel(master=self.frm_button, text='Filter View:')
        self.lbl_filter.grid(row=11, column=0, sticky='w', pady=(10, 0), padx=(15, 10))

        self.widget_categories = all_widget_categories(DEFAULT_VIEW_WIDGET_ATTRIBUTES)
        self.opm_properties_filter = ctk.CTkOptionMenu(master=self.frm_button,
                                                       values=self.widget_categories,
                                                       command=self.set_filtered_widget_display,
                                                       state=tk.DISABLED)
        self.opm_properties_filter.grid(row=12, column=0)
        if self.enable_tooltips:
            filter_view_tooltip = CTkToolTip(self.opm_properties_filter,
                                             wraplength=400,
                                             justify="left",
                                             message='Within the properties available for the selected view, you can '
                                                     'elect to filter the display further.')

        self.btn_refresh = ctk.CTkButton(master=button_frame, text='Refresh Preview',
                                         command=self.reload_preview,
                                         state=tk.DISABLED)
        self.btn_refresh.grid(row=14, column=0, padx=5, pady=(30, 0))
        if self.enable_tooltips:
            sync_tooltip = CTkToolTip(self.btn_refresh,
                                      wraplength=250,
                                      justify="left",
                                      message='The "Refresh Preview" button causes a reload of the preview panel, and '
                                              're-paints the preview, with the currently selected theme / appearance '
                                              'mode.')

        self.btn_reset = ctk.CTkButton(master=button_frame,
                                       text='Reset',
                                       state=tk.DISABLED,
                                       command=self.reset_theme)
        self.btn_reset.grid(row=15, column=0, padx=5, pady=(30, 5))

        self.btn_create = ctk.CTkButton(master=button_frame,
                                        text='New Theme',
                                        command=self.create_theme)
        self.btn_create.grid(row=16, column=0, padx=5, pady=(5, 5))

        self.btn_sync_modes = ctk.CTkButton(master=button_frame,
                                            text='Sync Modes',
                                            state=tk.DISABLED,
                                            command=self.sync_appearance_mode)
        self.btn_sync_modes.grid(row=17, column=0, padx=5, pady=(5, 5))
        if self.enable_tooltips:
            sync_tooltip = CTkToolTip(self.btn_sync_modes,
                                      wraplength=250,
                                      justify="left",
                                      message='Copies the color settings of the selected widget properties, for the '
                                              'currently selected Appearance Mode ("Dark"/"Light"), to its counterpart '
                                              'mode.')

        self.btn_sync_palette = ctk.CTkButton(master=button_frame,
                                              text='Sync Palette',
                                              state=tk.DISABLED,
                                              command=self.sync_theme_palette)
        self.btn_sync_palette.grid(row=18, column=0, padx=5, pady=(5, 5))
        if self.enable_tooltips:
            sync_tooltip = CTkToolTip(self.btn_sync_modes,
                                      wraplength=250,
                                      justify="left",
                                      message='Copies the Theme Palette color settings of the selected appearance '
                                              'mode ("Light"/"Dark") to its counterpart mode')

        self.btn_save = ctk.CTkButton(master=button_frame,
                                      text='Save',
                                      state=tk.DISABLED,
                                      command=self.save_theme)
        self.btn_save.grid(row=21, column=0, padx=5, pady=(30, 5))

        self.btn_save_as = ctk.CTkButton(master=button_frame,
                                         text='Save As',
                                         state=tk.DISABLED,
                                         command=self.save_theme_as)
        self.btn_save_as.grid(row=22, column=0, padx=5, pady=(5, 5))

        self.btn_delete = ctk.CTkButton(master=button_frame,
                                        text='Delete',
                                        state=tk.DISABLED,
                                        command=self.delete_theme)
        self.btn_delete.grid(row=23, column=0, padx=5, pady=(5, 5))

        btn_quit = ctk.CTkButton(master=button_frame, text='Quit', command=self.close_panels)
        btn_quit.grid(row=30, column=0, padx=5, pady=(60, 5))

        self.create_menu()

        if int(base_min_version) > int(base_ctk_version):
            print(f'WARNING: The version of CustomTkinter, on your system, is incompatible. Please upgrade to '
                  f'CustomTkinter {self.min_ctk_version} or later.')
            confirm = CTkMessagebox(master=self.ctk_control_panel,
                                    title='Please Upgrade CustomTkinter',
                                    message=f'The version of CustomTkinter, on your system, is incompatible. '
                                            f'Please upgrade to CustomTkinter {self.min_ctk_version} or later.',
                                    option_1='OK')
            if confirm.get() == 'OK':
                exit(1)

        self.load_theme()

        self.ctk_control_panel.mainloop()

    def flip_appearance_modes(self):
        confirm = CTkMessagebox(master=self.ctk_control_panel,
                                title='Confirm Action',
                                message=f'This will swap around, all of the theme appearance mode colours, between '
                                        f'Light mode and Dark mode. Are you sure you wish to proceed?',
                                options=["Yes", "No"])
        response = confirm.get()
        if response == 'No':
            return
        theme_json_file = self.theme_json_dir / self.theme_file
        mod.flip_appearance_modes(theme_file_path=theme_json_file)
        self.load_theme()

    def set_widget_colour(self, widget_property, new_colour):
        """Update the widget colour on the preview panel."""
        if not new_colour:
            # We should never see this message, but still...
            print('ERROR: set_widget_colour called without cause.')
            return
        if not cbtk.valid_colour(new_colour):
            self.status_bar.set_status_text(status_text=f'Paste action ignored - not a valid colour code.')
            return
        prev_colour = self.widgets[widget_property]["colour"]
        self.widgets[widget_property]['button'].configure(fg_color=new_colour)
        self.widgets[widget_property]['colour'] = new_colour
        appearance_mode_index = cbtk.str_mode_to_int(self.appearance_mode)
        # At this point widget_property is a concatenation of the widget type and widget property.
        # We need to split these out. The widget_property_split function, transforms these for us.
        widget_type, split_property = mod.widget_property_split(widget_property=widget_property)
        json_widget_type = mod.json_widget_type(widget_type=widget_type)
        self.theme_json_data[json_widget_type][split_property][appearance_mode_index] = new_colour
        parameters = []

        if prev_colour != new_colour and widget_property in ControlPanel.FORCE_REFRESH_PROPERTIES:
            # Then either this isn't a real widget, or is a property which cannot be updated
            # dynamically, and so we force a refresh to update the widgets dependent upon its properties.
            self.refresh_preview()
        elif prev_colour != new_colour:
            self.json_state = 'dirty'
            self.set_option_states()
            parameters.append(widget_type)
            parameters.append(split_property)
            parameters.append(new_colour)
            self.send_command_json(command_type='colour',
                                   command='update_widget_colour',
                                   parameters=parameters)

    def create_theme_palette(self, theme_name):
        self.theme_palette = mod.json_dict(json_file_path=ETC_DIR / 'default_palette.json')
        palette_json = theme_name.replace('.json', '') + '.json'
        self.palette_file = self.palettes_dir / palette_json
        with open(self.palette_file, "w") as f:
            json.dump(self.theme_palette, f, indent=2)

    def create_menu(self):
        # Set up the core of our menu
        self.des_menu = cbtk.CBtkMenu(self.ctk_control_panel, tearoff=0)
        foreground = cbtk.get_color_from_name(widget_type='CTkLabel', widget_property='text_color')
        background = cbtk.get_color_from_name(widget_type='CTkToplevel', widget_property='fg_color')
        self.ctk_control_panel.config(menu=self.des_menu)

        # Now add a File sub-menu option
        self.file_menu = cbtk.CBtkMenu(self.des_menu, tearoff=0)
        self.des_menu.add_cascade(label='File', menu=self.file_menu)
        self.file_menu.add_command(label='Refresh Preview', command=self.reload_preview)
        self.file_menu.add_separator()
        self.file_menu.add_command(label='Reset', command=self.reset_theme)
        self.file_menu.add_command(label='New Theme', command=self.create_theme)
        self.file_menu.add_command(label='Sync Modes', command=self.sync_appearance_mode)
        self.file_menu.add_command(label='Flip Modes', command=self.flip_appearance_modes)
        self.file_menu.add_command(label='Sync Palette', command=self.sync_theme_palette)
        self.file_menu.add_separator()
        self.file_menu.add_command(label='Save', command=self.save_theme)
        self.file_menu.add_command(label='Save As', command=self.save_theme_as)

        self.file_menu.add_separator()
        self.file_menu.add_command(label='Delete', command=self.delete_theme)
        self.file_menu.add_separator()
        self.file_menu.add_command(label='Provenance', command=self.launch_provenance_dialog)
        self.file_menu.add_separator()
        self.file_menu.add_command(label='Quit', command=self.close_panels)

        # Now add a Tools sub-menu option
        self.tools_menu = cbtk.CBtkMenu(self.des_menu, tearoff=0)
        self.des_menu.add_cascade(label='Tools', menu=self.tools_menu)
        self.tools_menu.add_command(label='Preferences', command=self.launch_preferences_dialog)
        self.tools_menu.add_command(label='Colour Harmonics', command=self.launch_harmony_dialog, state=tk.DISABLED)
        self.tools_menu.add_command(label='Merge Themes', command=self.launch_merge_dialog)

        self.tools_menu.add_command(label='About', command=self.about)

        self.set_option_states()

    def copy_property_colour(self, event=None, widget_property=None):
        colour = None
        try:
            colour = self.widgets[widget_property]['button'].cget('fg_color')
        except KeyError:
            self.status_bar.set_status_text(
                status_text=f'ERROR: Key Error on shade copy: Widget Property = {widget_property}')
            print(f'ERROR: Key Error on shade copy: Widget Property = {widget_property}')
        if colour:
            pyperclip.copy(colour)
            message = f'Colour {colour} copied to clipboard.'
            self.status_bar.set_status_text(status_text=message)
        elif not colour:
            self.status_bar.set_status_text(
                status_text=f'Copy for {colour} failed!')

    def about(self):

        widget_corner_radius = 5
        top_about = ctk.CTkToplevel(self.ctk_control_panel)
        top_about.title('About CTk Theme Builder')
        top_about.geometry('380x250')
        logo_image = cbtk.load_image(light_image=APP_IMAGES / 'bear-logo-colour.jpg', image_size=(200, 200))
        # Make preferences dialog modal
        top_about.rowconfigure(0, weight=1)
        top_about.rowconfigure(1, weight=0)
        top_about.columnconfigure(0, weight=1)

        frm_main = ctk.CTkFrame(master=top_about, corner_radius=widget_corner_radius)
        frm_main.grid(column=0, row=0, sticky='nsew')
        frm_main.columnconfigure(1, weight=1)
        frm_main.rowconfigure(0, weight=1)
        frm_main.rowconfigure(1, weight=0)

        frm_widgets = ctk.CTkFrame(master=frm_main, corner_radius=widget_corner_radius)
        frm_widgets.grid(column=0, row=0, padx=10, pady=10, sticky='nsew')

        frm_logo = ctk.CTkFrame(master=frm_main, corner_radius=widget_corner_radius)
        frm_logo.grid(column=1, row=0, padx=10, pady=10, sticky='nsew')

        lbl_title = ctk.CTkLabel(master=frm_widgets, text=f'{__title__}')
        lbl_title.grid(row=0, column=0, pady=(35, 10), sticky='ew')

        lbl_version = ctk.CTkLabel(master=frm_widgets, text=f'Version: {__version__}')
        lbl_version.grid(row=1, column=0, padx=10, sticky='ew')

        lbl_ctk_version = ctk.CTkLabel(master=frm_widgets, text=f'CustomTkinter: {ctk.__version__}')
        lbl_ctk_version.grid(row=2, column=0, padx=10, sticky='ew')

        lbl_author = ctk.CTkLabel(master=frm_widgets, text=f'Author: {__author__}')
        lbl_author.grid(row=3, column=0, padx=10, sticky='e')

        btn_logo = ctk.CTkButton(master=frm_logo, text='', height=50, width=50, corner_radius=widget_corner_radius,
                                 image=logo_image)
        btn_logo.grid(row=0, column=1, sticky='ew')

        frm_buttons = ctk.CTkFrame(master=frm_main, corner_radius=widget_corner_radius)
        frm_buttons.grid(column=0, row=1, padx=(5, 5), pady=(0, 0), sticky='ew', columnspan=2)

        btn_ok = ctk.CTkButton(master=frm_buttons, text='OK', width=355,
                               corner_radius=widget_corner_radius,
                               command=top_about.destroy)
        btn_ok.grid(row=0, column=0, padx=(5, 5), pady=10)
        top_about.resizable(False, False)

        top_about.grab_set()

    def launch_merge_dialog(self):
        self.top_merge = ctk.CTkToplevel(self.ctk_control_panel)
        self.top_merge.title('Merge Themes')
        self.top_merge.geometry('570x340')
        # Make sure the TopLevel doesn't disappear if we need to
        # open the tk.filedialog.askdirectory dialog to set a new theme folder.
        self.top_merge.transient(self.ctk_control_panel)
        # Make preferences dialog modal
        self.top_merge.rowconfigure(0, weight=1)
        self.top_merge.rowconfigure(1, weight=0)
        self.top_merge.columnconfigure(0, weight=1)

        frm_main = ctk.CTkFrame(master=self.top_merge, corner_radius=10)
        frm_main.grid(column=0, row=0, sticky='nsew')
        frm_main.columnconfigure(0, weight=1)
        frm_main.rowconfigure(0, weight=1)

        frm_main = ctk.CTkFrame(master=self.top_merge, corner_radius=10)
        frm_main.grid(column=0, row=0, sticky='nsew')
        frm_main.columnconfigure(0, weight=1)
        frm_main.rowconfigure(0, weight=1)

        frm_widgets = ctk.CTkFrame(master=frm_main, corner_radius=10)
        frm_widgets.grid(column=0, row=0, padx=5, pady=5, sticky='nsew')

        frm_buttons = ctk.CTkFrame(master=frm_main, corner_radius=0)
        frm_buttons.grid(column=0, row=1, padx=0, pady=(0, 0), sticky='ew')

        widget_start_row = 0

        lbl_primary_theme = ctk.CTkLabel(master=frm_widgets, text='Primary Theme', justify="right")
        lbl_primary_theme.grid(row=widget_start_row, column=0, padx=5, pady=(20, 5), sticky='e')

        if self.enable_tooltips:
            btn_author_tooltip = CTkToolTip(lbl_primary_theme,
                                            wraplength=250,
                                            justify="left",
                                            message="The primary theme to merge. The non-colour properties are, "
                                                    "adopted from the primary theme.")

        self.tk_primary_theme = tk.StringVar()
        self.opm_primary_theme = ctk.CTkOptionMenu(master=frm_widgets,
                                                   variable=self.tk_primary_theme,
                                                   values=self.app_themes_list())
        self.opm_primary_theme.grid(row=widget_start_row, column=1, padx=(0, 10), pady=(20, 5), sticky='w')

        lbl_primary_mode = ctk.CTkLabel(master=frm_widgets, text='Appearance Mode', justify="right")
        lbl_primary_mode.grid(row=widget_start_row, column=2, padx=5, pady=(20, 5), sticky='e')

        # The primary_theme_mode holds the CustomTkinter appearance mode (Dark / Light)
        self.tk_appearance_mode_var = tk.StringVar()
        rdo_primary_light = ctk.CTkRadioButton(master=frm_widgets, text='Light',
                                               variable=self.tk_appearance_mode_var,
                                               value='Light')
        rdo_primary_light.grid(row=widget_start_row, column=3, pady=(20, 5), sticky='w')
        widget_start_row += 1

        rdo_primary_dark = ctk.CTkRadioButton(master=frm_widgets, text='Dark', variable=self.tk_appearance_mode_var,
                                              value='Dark')
        rdo_primary_dark.grid(row=widget_start_row, column=3, pady=5, sticky='w')

        rdo_primary_dark.deselect()
        rdo_primary_light.select()

        widget_start_row += 1

        ###
        lbl_secondary_theme = ctk.CTkLabel(master=frm_widgets, text='Secondary Theme', justify="right")
        lbl_secondary_theme.grid(row=widget_start_row, column=0, padx=5, pady=(20, 5), sticky='e')

        if self.enable_tooltips:
            btn_author_tooltip = CTkToolTip(lbl_secondary_theme,
                                            wraplength=250,
                                            justify="left",
                                            message="The secondary theme to merge. The non-colour properties are, "
                                                    "adopted from the secondary theme.")

        self.tk_secondary_theme = tk.StringVar()
        self.opm_secondary_theme = ctk.CTkOptionMenu(master=frm_widgets,
                                                     variable=self.tk_secondary_theme,
                                                     values=self.app_themes_list())
        self.opm_secondary_theme.grid(row=widget_start_row, column=1, padx=(0, 10), pady=(20, 5), sticky='w')

        lbl_secondary_mode = ctk.CTkLabel(master=frm_widgets, text='Appearance Mode', justify="right")
        lbl_secondary_mode.grid(row=widget_start_row, column=2, padx=5, pady=(20, 5), sticky='e')

        # The secondary_theme_mode holds the CustomTkinter appearance mode (Dark / Light)
        self.tk_appearance_mode_var = tk.StringVar()
        rdo_secondary_light = ctk.CTkRadioButton(master=frm_widgets, text='Light',
                                                 variable=self.tk_appearance_mode_var,
                                                 value='Light')
        rdo_secondary_light.grid(row=widget_start_row, column=3, pady=(20, 5), sticky='w')
        widget_start_row += 1

        rdo_secondary_dark = ctk.CTkRadioButton(master=frm_widgets, text='Dark',
                                                variable=self.tk_appearance_mode_var,
                                                value='Dark')
        rdo_secondary_dark.grid(row=widget_start_row, column=3, pady=5, sticky='w')

        rdo_secondary_dark.deselect()
        rdo_secondary_light.select()

        widget_start_row += 1
        lbl_new_theme_name = ctk.CTkLabel(master=frm_widgets, text='New theme name', justify="right")
        lbl_new_theme_name.grid(row=widget_start_row, column=0, padx=5, pady=(30, 5), sticky='e')

        self.tk_theme_name = tk.StringVar()
        self.ent_theme_name = ctk.CTkEntry(master=frm_widgets,
                                           textvariable=self.tk_theme_name,
                                           width=160)
        self.ent_theme_name.grid(row=widget_start_row, column=1, padx=(0, 0), pady=(30, 5), sticky='w')

        if self.enable_tooltips:
            btn_author_tooltip = CTkToolTip(lbl_new_theme_name,
                                            wraplength=250,
                                            justify="left",
                                            message="The target theme name is included to the theme JSON, in the "
                                                    "provenance section.")

        lbl_new_theme_file = ctk.CTkLabel(master=frm_widgets, text='File name', justify="right")
        lbl_new_theme_file.grid(row=widget_start_row, column=2, padx=5, pady=(30, 5), sticky='e')

        self.tk_theme_file = tk.StringVar()
        self.ent_theme_file = ctk.CTkEntry(master=frm_widgets,
                                           textvariable=self.tk_theme_file,
                                           width=160)
        self.ent_theme_file.grid(row=widget_start_row, column=3, padx=(0, 0), pady=(30, 5), sticky='w')

        if self.enable_tooltips:
            btn_author_tooltip = CTkToolTip(lbl_new_theme_file,
                                            wraplength=250,
                                            justify="left",
                                            message="Enter the file name (prefix only), of the new theme file.")

        widget_start_row += 1
        self.tk_open_on_merge = tk.IntVar(master=frm_widgets)
        self.swt_open_on_merge = ctk.CTkSwitch(master=frm_widgets,
                                               text='Open on merge',
                                               variable=self.tk_open_on_merge,
                                               command=self.get_single_click_paste_setting)
        self.swt_open_on_merge.grid(row=widget_start_row, column=3, padx=(0, 0), pady=(20, 10), sticky='w')

        if self.enable_tooltips:
            btn_enable_tooltips_tooltip = CTkToolTip(self.swt_open_on_merge,
                                                     wraplength=400,
                                                     message="Enable this switch, if you wish to open the merged theme.")

        widget_start_row += 1

        # Control buttons
        btn_close = ctk.CTkButton(master=frm_buttons, text='Cancel', command=self.top_merge.destroy)
        btn_close.grid(row=0, column=0, padx=(15, 35), pady=5)

        btn_save = ctk.CTkButton(master=frm_buttons, text='Save', command=self.save_preferences)
        btn_save.grid(row=0, column=1, padx=(150, 15), pady=5)
        self.top_merge.grab_set()

    def launch_preferences_dialog(self):
        self.top_prefs = ctk.CTkToplevel(self.ctk_control_panel)
        self.top_prefs.title('CTk Theme Builder Preferences')
        self.top_prefs.geometry('500x550')
        # Make sure the TopLevel doesn't disappear if we need to
        # open the tk.filedialog.askdirectory dialog to set a new theme folder.
        self.top_prefs.transient(self.ctk_control_panel)
        # Make preferences dialog modal
        self.top_prefs.rowconfigure(0, weight=1)
        self.top_prefs.rowconfigure(1, weight=0)
        self.top_prefs.columnconfigure(0, weight=1)

        frm_main = ctk.CTkFrame(master=self.top_prefs, corner_radius=10)
        frm_main.grid(column=0, row=0, sticky='nsew')
        frm_main.columnconfigure(0, weight=1)
        frm_main.rowconfigure(0, weight=1)

        frm_main = ctk.CTkFrame(master=self.top_prefs, corner_radius=10)
        frm_main.grid(column=0, row=0, sticky='nsew')
        frm_main.columnconfigure(0, weight=1)
        frm_main.rowconfigure(0, weight=1)

        frm_widgets = ctk.CTkFrame(master=frm_main, corner_radius=10)
        frm_widgets.grid(column=0, row=0, padx=5, pady=5, sticky='nsew')

        frm_buttons = ctk.CTkFrame(master=frm_main, corner_radius=0)
        frm_buttons.grid(column=0, row=1, padx=0, pady=(0, 0), sticky='ew')

        widget_start_row = 0
        lbl_author_name = ctk.CTkLabel(master=frm_widgets, text='Author', justify="right")
        lbl_author_name.grid(row=widget_start_row, column=0, padx=5, pady=(30, 5), sticky='e')

        if not self.theme_author:
            self.theme_author = self.user_name
        self.tk_author_name = tk.StringVar(value=self.theme_author)
        self.ent_author_name = ctk.CTkEntry(master=frm_widgets,
                                            textvariable=self.tk_author_name,
                                            width=160)
        self.ent_author_name.grid(row=widget_start_row, column=1, padx=(0, 0), pady=(30, 5), sticky='w')

        if self.enable_tooltips:
            btn_author_tooltip = CTkToolTip(lbl_author_name,
                                            wraplength=250,
                                            justify="left",
                                            message="The author's name is included to the theme JSON, in the "
                                                    "provenance section.")

        widget_start_row += 1
        lbl_theme = ctk.CTkLabel(master=frm_widgets, text='Cntrl Panel Theme', justify="right")
        lbl_theme.grid(row=widget_start_row, column=0, padx=5, pady=(0, 5), sticky='e')

        if self.enable_tooltips:
            btn_author_tooltip = CTkToolTip(lbl_theme,
                                            wraplength=250,
                                            justify="left",
                                            message="The default theme for the CTk Theme Builder control panel, "
                                                    "is GreyGhost, however you can override this here.")

        control_panel_theme = os.path.splitext(self.control_panel_theme)[0]
        control_panel_theme = os.path.basename(control_panel_theme)
        self.tk_control_panel_theme = tk.StringVar(value=control_panel_theme)
        self.opm_control_panel_theme = ctk.CTkOptionMenu(master=frm_widgets,
                                                         variable=self.tk_control_panel_theme,
                                                         values=self.app_themes_list())
        self.opm_control_panel_theme.grid(row=widget_start_row, column=1, padx=0, pady=5, sticky='w')
        widget_start_row += 1

        lbl_mode = ctk.CTkLabel(master=frm_widgets, text='Appearance Mode', justify="right")
        lbl_mode.grid(row=widget_start_row, column=0, padx=5, sticky='e')

        # The control_panel_mode holds the  CustomTkinter appearance mode (Dark / Light)
        self.tk_appearance_mode_var = tk.StringVar(value=self.control_panel_mode)
        rdo_light = ctk.CTkRadioButton(master=frm_widgets, text='Light', variable=self.tk_appearance_mode_var,
                                       value='Light')
        rdo_light.grid(row=widget_start_row, column=1, sticky='w')
        widget_start_row += 1

        rdo_dark = ctk.CTkRadioButton(master=frm_widgets, text='Dark', variable=self.tk_appearance_mode_var,
                                      value='Dark')
        rdo_dark.grid(row=widget_start_row, column=1, pady=5, sticky='w')
        widget_start_row += 1

        if self.control_panel_mode == 'Dark':
            rdo_light.deselect()
            rdo_dark.select()
        elif self.control_panel_mode == 'Light':
            rdo_dark.deselect()
            rdo_light.select()

        # lbl_enable_tooltips = ctk.CTkLabel(master=frm_widgets, text='Enable tooltips', justify="right")
        # lbl_enable_tooltips.grid(row=widget_start_row, column=0, padx=5, sticky='e')

        self.tk_enable_tooltips = tk.IntVar(master=frm_widgets)
        self.tk_enable_tooltips.set(self.enable_tooltips)
        self.swt_enable_tooltips = ctk.CTkSwitch(master=frm_widgets,
                                                 text='Tooltips',
                                                 variable=self.tk_enable_tooltips,
                                                 command=self.get_tooltips_setting)
        self.swt_enable_tooltips.grid(row=widget_start_row, column=1, padx=(0, 0), pady=10, sticky='w')
        widget_start_row += 1

        self.tk_enable_palette_labels = tk.IntVar(master=frm_widgets)
        self.tk_enable_palette_labels.set(self.enable_palette_labels)
        self.swt_enable_palette_labels = ctk.CTkSwitch(master=frm_widgets,
                                                       text='Colour Palette Labels',
                                                       variable=self.tk_enable_palette_labels,
                                                       command=self.get_palette_label_setting)
        self.swt_enable_palette_labels.grid(row=widget_start_row, column=1, padx=(0, 0), pady=10, sticky='w')

        if self.enable_tooltips:
            btn_enable_palette_labels_tooltip = CTkToolTip(self.swt_enable_palette_labels,
                                                           "Enable/disable the rendering of the colour palette "
                                                           "labels.")

        widget_start_row += 1
        self.tk_last_theme_on_start = tk.IntVar(master=frm_widgets, value=self.last_theme_on_start)
        self.tk_last_theme_on_start.set(self.last_theme_on_start)
        self.swt_last_theme_on_start = ctk.CTkSwitch(master=frm_widgets,
                                                     text='Load Last Theme',
                                                     variable=self.tk_last_theme_on_start,
                                                     command=self.get_last_theme_on_start)
        self.swt_last_theme_on_start.grid(row=widget_start_row, column=1, padx=(0, 0), pady=10, sticky='w')
        if self.enable_tooltips:
            last_theme_on_start_tooltip = CTkToolTip(self.swt_last_theme_on_start,
                                                     wraplength=250,
                                                     justify="left",
                                                     message="Enable this switch, to auto-select the last theme "
                                                             "you worked on, at application startup.")

        widget_start_row += 1
        self.tk_enable_single_click_paste = tk.IntVar(master=frm_widgets)
        self.tk_enable_single_click_paste.set(self.enable_single_click_paste)
        self.swt_enable_single_click_paste = ctk.CTkSwitch(master=frm_widgets,
                                                           text='Single Click Paste',
                                                           variable=self.tk_enable_single_click_paste,
                                                           command=self.get_single_click_paste_setting)
        self.swt_enable_single_click_paste.grid(row=widget_start_row, column=1, padx=(0, 0), pady=10, sticky='w')

        widget_start_row += 1
        if self.enable_tooltips:
            btn_enable_tooltips_tooltip = CTkToolTip(self.swt_enable_single_click_paste,
                                                     wraplength=400,
                                                     message="Enable/disable colour pasting, via a single click. "
                                                             "Colours can be pasted to the colour palette or the array "
                                                             "of widget colour properties.")
        widget_start_row += 1

        lbl_shade_adjust_differential = ctk.CTkLabel(master=frm_widgets, text='Adjust Shade Step', justify="right")
        lbl_shade_adjust_differential.grid(row=widget_start_row, column=0, padx=5, pady=(0, 0), sticky='e')

        self.opm_shade_adjust_differential = ctk.CTkOptionMenu(master=frm_widgets,
                                                               width=12,
                                                               values=['1', '2', '3', '4', '5', '6', '7', '8', '9'])
        self.opm_shade_adjust_differential.grid(row=widget_start_row, column=1, padx=0, pady=5, sticky='w')
        self.opm_shade_adjust_differential.set(str(self.shade_adjust_differential))
        widget_start_row += 1

        widget_start_row += 1

        lbl_harmony_contrast_differential = ctk.CTkLabel(master=frm_widgets, text='Harmony Shade Step', justify="right")
        lbl_harmony_contrast_differential.grid(row=widget_start_row, column=0, padx=(30, 5), pady=(0, 0), sticky='e')

        self.opm_harmony_contrast_differential = ctk.CTkOptionMenu(master=frm_widgets,
                                                                   width=12,
                                                                   values=['1', '2', '3', '5', '6', '7', '8', '9'])
        self.opm_harmony_contrast_differential.grid(row=widget_start_row, column=1, padx=0, pady=5, sticky='w')
        self.opm_harmony_contrast_differential.set(str(self.harmony_contrast_differential))
        widget_start_row += 1

        self.folder_image = cbtk.load_image(light_image=APP_IMAGES / 'folder.png', image_size=(20, 20))
        lbl_theme_json_dir = ctk.CTkLabel(master=frm_widgets, text='Themes Location', justify="right")
        lbl_theme_json_dir.grid(row=widget_start_row, column=0, padx=5, pady=5, sticky='e')

        if self.enable_tooltips:
            lbl_theme_json_dir_tooltip = CTkToolTip(lbl_theme_json_dir,
                                                    "Select a location to store your themes.")

        btn_theme_json_dir = ctk.CTkButton(master=frm_widgets,
                                           text='',
                                           width=30,
                                           height=30,
                                           fg_color='#748696',
                                           image=self.folder_image,
                                           command=self.preferred_json_location)
        btn_theme_json_dir.grid(row=widget_start_row, column=1, pady=5, sticky='w')
        widget_start_row += 1

        self.lbl_pref_theme_dir_disp = ctk.CTkLabel(master=frm_widgets, text=self.theme_json_dir, justify="right",
                                                    font=mod.SMALL_TEXT)
        self.lbl_pref_theme_dir_disp.grid(row=widget_start_row, column=1, padx=5, pady=5, sticky='e')
        widget_start_row += 1

        # Control buttons
        btn_close = ctk.CTkButton(master=frm_buttons, text='Cancel', command=self.top_prefs.destroy)
        btn_close.grid(row=0, column=0, padx=(15, 35), pady=5)

        btn_save = ctk.CTkButton(master=frm_buttons, text='Save', command=self.save_preferences)
        btn_save.grid(row=0, column=1, padx=(150, 15), pady=5)
        self.top_prefs.grab_set()

    def launch_provenance_dialog(self):
        self.top_prov = ctk.CTkToplevel(self.ctk_control_panel)
        self.top_prov.title('Theme Provenance')
        self.top_prov.geometry('580x470')
        # Make sure we pop up in front of Control Panel
        self.top_prov.transient(self.ctk_control_panel)
        self.top_prov.rowconfigure(1, weight=1)

        frm_header = ctk.CTkFrame(master=self.top_prov)
        frm_header.grid(column=0, row=0, padx=5, pady=5, sticky='nsew')

        frm_widgets = ctk.CTkFrame(master=self.top_prov)
        frm_widgets.grid(column=0, row=1, padx=5, pady=5, sticky='nsew')

        frm_buttons = ctk.CTkFrame(master=self.top_prov)
        frm_buttons.grid(column=0, row=2, padx=5, pady=5, sticky='ew')

        theme_name = self.theme_json_data["provenance"]["theme name"]
        created_with = self.theme_json_data["provenance"]["created with"]
        created_label = self.theme_json_data["provenance"]["date created"]
        authors_name = self.theme_json_data["provenance"]["theme author"]
        last_modified_by = self.theme_json_data["provenance"]["last modified by"]
        last_modified = self.theme_json_data["provenance"]["last modified"]
        harmony_method = self.theme_json_data["provenance"]["harmony method"]
        keystone_colour = self.theme_json_data["provenance"]["keystone colour"]

        widget_row = 0
        # Header -  Theme Name (frm_header)
        lbl_theme_label = ctk.CTkLabel(master=frm_header, text='Theme:', width=280, anchor="e", font=HEADING4)
        lbl_theme_label.grid(row=widget_row, column=0, padx=5, pady=10, sticky='e', columnspan=2)

        lbl_theme_name = ctk.CTkLabel(master=frm_header, text=f'{theme_name}', justify="left", font=HEADING4)
        lbl_theme_name.grid(row=widget_row, column=2, padx=5, pady=10, sticky='w', columnspan=2)

        # Start the main body of the dialog (frm_widgets)
        # Creation Details
        widget_row += 1
        lbl_author_label = ctk.CTkLabel(master=frm_widgets, text='Author:', anchor="e", width=75)
        lbl_author_label.grid(row=widget_row, column=0, padx=20, pady=10, sticky='e')

        lbl_author_name = ctk.CTkLabel(master=frm_widgets, text=f'{authors_name}', anchor="w")
        lbl_author_name.grid(row=widget_row, column=1, padx=5, pady=10, sticky='w')

        lbl_created_label = ctk.CTkLabel(master=frm_widgets, text='Created:', width=100, anchor="e")
        lbl_created_label.grid(row=widget_row, column=2, padx=5, pady=10, sticky='e')

        lbl_created_date = ctk.CTkLabel(master=frm_widgets, text=f'{created_label}', anchor="w", width=75)
        lbl_created_date.grid(row=widget_row, column=3, padx=(20, 30), pady=10, sticky='w')

        # Modification Details
        widget_row += 1
        lbl_modified_by_label = ctk.CTkLabel(master=frm_widgets, text='Last modified:', anchor="e")
        lbl_modified_by_label.grid(row=widget_row, column=0, padx=20, pady=10, sticky='e')

        lbl_modified_by_name = ctk.CTkLabel(master=frm_widgets, text=f'{last_modified_by}', anchor="w")
        lbl_modified_by_name.grid(row=widget_row, column=1, padx=5, pady=10, sticky='w')

        lbl_last_modified_label = ctk.CTkLabel(master=frm_widgets, text='Date:', width=75, anchor="e")
        lbl_last_modified_label.grid(row=widget_row, column=2, padx=5, pady=10, sticky='e')

        lbl_last_modified_date = ctk.CTkLabel(master=frm_widgets, text=f'{last_modified}', anchor="w")
        lbl_last_modified_date.grid(row=widget_row, column=3, padx=20, pady=10, sticky='w')

        # Keystone Details
        widget_row += 1
        lbl_keystone_method_label = ctk.CTkLabel(master=frm_widgets, text='Harmony method:', width=75, anchor="e")
        lbl_keystone_method_label.grid(row=widget_row, column=0, padx=20, pady=10, sticky='e')

        lbl_keystone_method = ctk.CTkLabel(master=frm_widgets, text=f'{harmony_method}', anchor="w")
        lbl_keystone_method.grid(row=widget_row, column=1, padx=5, pady=10, sticky='w')

        widget_row += 1
        lbl_keystone_colour_label = ctk.CTkLabel(master=frm_widgets, text='Keystone colour:', width=75, anchor="e")
        lbl_keystone_colour_label.grid(row=widget_row, column=0, padx=20, pady=10, sticky='e')

        lbl_keystone_colour = ctk.CTkLabel(master=frm_widgets, text=f'{keystone_colour}', anchor="w")
        lbl_keystone_colour.grid(row=widget_row, column=1, padx=5, pady=(10, 5), sticky='w')

        widget_row += 1
        btn_keystone_colour = ctk.CTkButton(master=frm_widgets,
                                            fg_color=keystone_colour,
                                            hover_color=keystone_colour,
                                            height=70,
                                            width=50,
                                            text=keystone_colour)
        btn_keystone_colour.grid(row=widget_row, column=1, padx=5, pady=(0, 5), sticky='w')

        # Created with...
        regular_italic = ctk.CTkFont(family="Roboto", size=13, slant="italic")
        widget_row += 1
        lbl_created_with_label = ctk.CTkLabel(master=frm_widgets, font=regular_italic,
                                              text='Built with:', width=75, anchor="e")
        lbl_created_with_label.grid(row=widget_row, column=2, padx=20, pady=(50, 10), sticky='e')

        lbl_created_with = ctk.CTkLabel(master=frm_widgets, font=regular_italic, text=f'{created_with}', anchor="w")
        lbl_created_with.grid(row=widget_row, column=3, padx=5, pady=(50, 10), sticky='w')

        # Add the close button into the bottom frame (frm_buttons).
        btn_close = ctk.CTkButton(master=frm_buttons, text='Close', command=self.top_prov.destroy, width=550)
        btn_close.grid(row=0, column=0, padx=10, pady=(5, 5), sticky='we')

    def save_theme_palette(self, theme_name=None):
        """Save the colour palette colours back to disk."""
        if theme_name is None:
            palette_json = self.palette_file
        else:
            palette_json = theme_name.replace('.json', '') + '.json'

        # Update the button colour settings to the self.theme_palette dictionary
        self.palette_file = self.palettes_dir / palette_json
        if self.appearance_mode.lower() == 'light':
            mode = 0
        else:
            mode = 1
        for entry_id, button in enumerate(self.theme_palette_tiles):
            fg_colour = self.theme_palette_tiles[entry_id].cget('fg_color')
            self.theme_palette[str(entry_id)][mode] = fg_colour

        with open(self.palette_file, "w") as f:
            json.dump(self.theme_palette, f, indent=2)

    def send_command_json(self, command_type: str, command: str, parameters: list = None):
        """Format our command into a JSON payload in string format. We have two command type. These are 'control' and
        'filter'. The parameters' parameter, can be used to accept a list to filter against, of a list to be used to pass
        parameters to a target function/method, in the Preview Panel."""
        if parameters is None:
            parameters = []

        parameters_str = ''
        for parameter in parameters:
            parameters_str = parameters_str + '"' + parameter + '", '
        parameters_str = parameters_str.rstrip(", ")

        if command == 'update_widget_colour':
            # We need to keep track of dirtied entries
            # so that we can re-render if we toggle
            # Light and Dark mode.
            widget_property = f'{parameters[0]}: {parameters[1]}'
            if parameters[0] != 'CTk':
                # With the exception of CTk(), we strip out the CTk string,
                # from the widget name, for display purposes.
                widget_property = widget_property.replace('CTk', '')
            mode = self.seg_mode.get()
            # So we update either light_status or
            # dark_status entry in our widgets dict.
            status_key = mode.lower() + '_status'
            self.widgets[widget_property][status_key] = 'dirty'

        message_json_str = '{ "command_type": "%command_type%",' \
                           ' "command": "%command%",' \
                           ' "parameters": [%parameters%] }'
        message_json_str = message_json_str.replace('%parameters%', parameters_str)

        message_json_str = message_json_str.replace('%command_type%', command_type)
        message_json_str = message_json_str.replace('%command%', command)
        self.send_message(message=message_json_str)

    @staticmethod
    def prepare_message(message):
        message = message.encode(ENCODING_FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(ENCODING_FORMAT)
        send_length += b' ' * (HEADER_SIZE - len(send_length))
        return send_length, message

    def send_message(self, message):

        listener_checks = 0
        listener_started = False
        while not listener_started:
            if LISTENER_FILE.exists():
                listener_started = True
            else:
                listener_checks += 1
            if listener_checks > 50:
                print('Timeout waiting for preview panel listener!')
                exit(1)
            time.sleep(0.1)

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connected = False
        connect_tries = 0
        while not connected:
            try:
                if connect_tries > 10:
                    print('Communication error sending message to preview panel!')
                    exit(1)
                connect_tries += 1
                client.connect(METHOD_LISTENER_ADDRESS)
                connected = True
            except ConnectionRefusedError:
                time.sleep(0.1)

        send_length, message = self.prepare_message(message)
        client.send(send_length)
        client.send(message)
        # print(f'Message sent: {message.decode(ENCODING_FORMAT)}')
        # The disconnect command has to follow the required JSON command format...
        send_length, message = self.prepare_message(DISCONNECT_JSON)
        client.send(send_length)
        client.send(message)
        client.close()

    def render_geometry_buttons(self):

        button_height = 40
        button_width = 100
        corner_radius = 10
        border_width = 3
        pad_x = (9, 9)
        pad_y = (5, 5)

        lbl_header = ctk.CTkLabel(master=self.frm_geometry,
                                  text=f'Widget Geometry',
                                  font=mod.HEADING4)
        lbl_header.grid(row=0,
                        column=0,
                        sticky='w',
                        columnspan=12,
                        pady=(5, 0),
                        padx=10)
        row = 1
        column = 0
        btn_geo_button = ctk.CTkButton(master=self.frm_geometry,
                                       text='Button',
                                       height=button_height,
                                       width=button_width,
                                       corner_radius=corner_radius,
                                       border_width=border_width,
                                       command=lambda: self.launch_widget_geometry('CTkButton'))
        btn_geo_button.grid(row=row,
                            column=column,
                            padx=pad_x,
                            pady=pad_y)
        column += 1

        btn_geo_checkbox = ctk.CTkButton(master=self.frm_geometry,
                                         text='Checkbox',
                                         height=button_height,
                                         width=button_width,
                                         corner_radius=corner_radius,
                                         border_width=border_width,
                                         command=lambda: self.launch_widget_geometry('CTkCheckBox'))
        btn_geo_checkbox.grid(row=row,
                              column=column,
                              padx=pad_x,
                              pady=pad_y)
        column += 1

        btn_geo_combobox = ctk.CTkButton(master=self.frm_geometry,
                                         text='ComboBox',
                                         height=button_height,
                                         width=button_width,
                                         corner_radius=corner_radius,
                                         border_width=border_width,
                                         command=lambda: self.launch_widget_geometry('CTkComboBox'))
        btn_geo_combobox.grid(row=row,
                              column=column,
                              padx=pad_x,
                              pady=pad_y)
        column += 1

        btn_geo_entry = ctk.CTkButton(master=self.frm_geometry,
                                      text='Entry',
                                      height=button_height,
                                      width=button_width,
                                      corner_radius=corner_radius,
                                      border_width=border_width,
                                      command=lambda: self.launch_widget_geometry('CTkEntry'))

        btn_geo_entry.grid(row=row,
                           column=column,
                           padx=pad_x,
                           pady=pad_y)
        column += 1

        btn_geo_frame = ctk.CTkButton(master=self.frm_geometry,
                                      text='Frame',
                                      height=button_height,
                                      width=button_width,
                                      corner_radius=corner_radius,
                                      border_width=border_width,
                                      command=lambda: self.launch_widget_geometry('CTkFrame'))
        btn_geo_frame.grid(row=row,
                           column=column,
                           padx=pad_x,
                           pady=pad_y)
        column += 1

        btn_geo_label = ctk.CTkButton(master=self.frm_geometry,
                                      text='Label',
                                      height=button_height,
                                      width=button_width,
                                      corner_radius=corner_radius,
                                      border_width=border_width,
                                      command=lambda: self.launch_widget_geometry('CTkLabel'))
        btn_geo_label.grid(row=row,
                           column=column,
                           padx=pad_x,
                           pady=pad_y)

        column += 1
        btn_geo_option_menu = ctk.CTkButton(master=self.frm_geometry,
                                            text='OptionMenu',
                                            height=button_height,
                                            width=button_width,
                                            corner_radius=corner_radius,
                                            border_width=border_width,
                                            command=lambda: self.launch_widget_geometry('CTkOptionMenu'))
        btn_geo_option_menu.grid(row=row,
                                 column=column,
                                 padx=pad_x,
                                 pady=pad_y)

        row += 1
        column = 0

        btn_geo_progress = ctk.CTkButton(master=self.frm_geometry,
                                         text='ProgressBar',
                                         height=button_height,
                                         width=button_width,
                                         corner_radius=corner_radius,
                                         border_width=border_width,
                                         command=lambda: self.launch_widget_geometry('CTkProgressBar'))
        btn_geo_progress.grid(row=row,
                              column=column,
                              padx=pad_x,
                              pady=pad_y)

        column += 1

        btn_geo_radio = ctk.CTkButton(master=self.frm_geometry,
                                      text='RadioButton',
                                      height=button_height,
                                      width=button_width,
                                      corner_radius=corner_radius,
                                      border_width=border_width,
                                      command=lambda: self.launch_widget_geometry('CTkRadioButton'))
        btn_geo_radio.grid(row=row,
                           column=column,
                           padx=pad_x,
                           pady=pad_y)

        column += 1

        btn_geo_scrollbar = ctk.CTkButton(master=self.frm_geometry,
                                          text='SegButton',
                                          height=button_height,
                                          width=button_width,
                                          corner_radius=corner_radius,
                                          border_width=border_width,
                                          command=lambda: self.launch_widget_geometry('CTkSegmentedButton'))
        btn_geo_scrollbar.grid(row=row,
                               column=column,
                               padx=pad_x,
                               pady=pad_y)

        column += 1

        btn_geo_scrollbar = ctk.CTkButton(master=self.frm_geometry,
                                          text='ScrollBar',
                                          height=button_height,
                                          width=button_width,
                                          corner_radius=corner_radius,
                                          border_width=border_width,
                                          command=lambda: self.launch_widget_geometry('CTkScrollbar'))
        btn_geo_scrollbar.grid(row=row,
                               column=column,
                               padx=pad_x,
                               pady=pad_y)
        column += 1

        btn_geo_slider = ctk.CTkButton(master=self.frm_geometry,
                                       text='Slider',
                                       height=button_height,
                                       width=button_width,
                                       corner_radius=corner_radius,
                                       border_width=border_width,
                                       command=lambda: self.launch_widget_geometry('CTkSlider'))
        btn_geo_slider.grid(row=row,
                            column=column,
                            padx=pad_x,
                            pady=pad_y)
        column += 1

        btn_geo_switch = ctk.CTkButton(master=self.frm_geometry,
                                       text='Switch',
                                       height=button_height,
                                       width=button_width,
                                       corner_radius=corner_radius,
                                       border_width=border_width,
                                       command=lambda: self.launch_widget_geometry('CTkSwitch'))
        btn_geo_switch.grid(row=row,
                            column=column,
                            padx=pad_x,
                            pady=pad_y)
        column += 1

        btn_geo_switch = ctk.CTkButton(master=self.frm_geometry,
                                       text='Textbox',
                                       height=button_height,
                                       width=button_width,
                                       corner_radius=corner_radius,
                                       border_width=border_width,
                                       command=lambda: self.launch_widget_geometry('CTkTextbox'))
        btn_geo_switch.grid(row=row,
                            column=column,
                            padx=pad_x,
                            pady=pad_y)
        column += 1

    def launch_widget_geometry(self, widget_type):
        def slider_callback(property_name, value):
            label_text = property_name.replace('_', ' ')
            base_label_text = label_text.replace(widget_type.lower(), '') + ': '
            property_value = int(value)
            label_dict[property_name].configure(text=base_label_text + str(property_value))
            config_param = property_name.replace(f'{widget_type.lower()}_', '')
            self.geometry_edit_values[property_name] = property_value

            if config_param == 'border_width_unchecked':
                geometry_widget.deselect()
            elif config_param == 'border_width_checked':
                geometry_widget.select()

            update_widget_geometry(widget=geometry_widget, widget_property=config_param, property_value=property_value)

        def deselect_widget(widget_id):
            widget_id.deselect()

        self.geometry_edit_values = {}
        preview_frame_top = self.theme_json_data['CTkFrame']['top_fg_color'][
            cbtk.str_mode_to_int(self.appearance_mode)]

        self.top_geometry = ctk.CTkToplevel(self.ctk_control_panel)
        self.top_geometry.title(f'{widget_type} Widget Geometry')

        self.restore_geom_geometry()

        # Make preferences dialog modal
        self.top_geometry.rowconfigure(0, weight=1)
        self.top_geometry.rowconfigure(1, weight=0)
        # self.top_geometry.columnconfigure(0, weight=0)
        # self.top_geometry.columnconfigure(1, weight=1)

        preview_text_colour = self.theme_json_data['CTkLabel']['text_color'][
            cbtk.str_mode_to_int(self.appearance_mode)]

        frm_main = ctk.CTkFrame(master=self.top_geometry, corner_radius=5)
        frm_main.grid(column=0, row=0, sticky='nsew')
        frm_main.columnconfigure(0, weight=0)
        frm_main.columnconfigure((1, 2), weight=1)
        frm_main.rowconfigure(0, weight=1)

        frame_fg_color = self.theme_json_data['CTkFrame']['fg_color'][
            cbtk.str_mode_to_int(self.appearance_mode)]
        json_widget_type = mod.json_widget_type(widget_type=widget_type)

        mode = cbtk.str_mode_to_int(self.appearance_mode)
        if widget_type == 'CTkFrame':
            self.top_geometry.geometry('764x280')
            frm_widget_preview_low = ctk.CTkFrame(master=frm_main,
                                                  fg_color=cbtk.contrast_colour(preview_frame_top, 20)
                                                  )
            frm_main.configure(corner_radius=self.theme_json_data[widget_type]['corner_radius'])
        else:
            frm_widget_preview_low = ctk.CTkFrame(master=frm_main,
                                                  corner_radius=5,
                                                  fg_color=preview_frame_top)

        frm_widget_preview_low.grid(column=1, row=0, padx=10, pady=10, sticky='nsew')

        frm_controls = ctk.CTkFrame(master=frm_main)
        frm_controls.grid(column=0, row=0, padx=10, pady=10, sticky='nsew')

        frm_buttons = ctk.CTkFrame(master=frm_main)
        frm_buttons.grid(column=0, row=1, padx=10, pady=(0, 10), sticky='ew')

        frm_label = ctk.CTkFrame(master=frm_main)
        frm_label.grid(column=1, row=1, padx=10, pady=(0, 10), sticky='ew')

        widget_label = ctk.CTkLabel(master=frm_label, text=f'{widget_type} Geometry',
                                    font=mod.HEADING5,
                                    justify=ctk.CENTER)
        widget_label.grid(row=0, column=0, padx=(30, 30), sticky='ew')

        # Control buttons
        btn_close = ctk.CTkButton(master=frm_buttons, text='Cancel', command=self.close_geometry_dialog)
        btn_close.grid(row=0, column=0, padx=(25, 35), pady=5)

        btn_save = ctk.CTkButton(master=frm_buttons, text='Save',
                                 command=lambda w_type=widget_type: self.save_geometry_edits(widget_type=w_type))
        btn_save.grid(row=0, column=1, padx=(160, 15), pady=5)

        geometry_parameters_file = str(ETC_DIR / 'geometry_parameters.json')
        geometry_parameters_file = Path(geometry_parameters_file)
        geometry_parameters_file_json = mod.json_dict(json_file_path=geometry_parameters_file)

        if widget_type == 'CTkButton':
            self.top_geometry.geometry('764x234')
            button_text_colour = self.theme_json_data[json_widget_type]['text_color'][mode]
            button_fg_colour = self.theme_json_data[json_widget_type]['fg_color'][mode]
            button_hover_colour = self.theme_json_data[json_widget_type]['hover_color'][mode]
            button_border_colour = self.theme_json_data[json_widget_type]['border_color'][mode]

            geometry_widget = ctk.CTkButton(master=frm_widget_preview_low,
                                            text_color=button_text_colour,
                                            fg_color=button_fg_colour,
                                            hover_color=button_hover_colour,
                                            border_color=button_border_colour,
                                            text='CTkButton',
                                            corner_radius=self.theme_json_data['CTkButton']['corner_radius'],
                                            border_width=self.theme_json_data['CTkButton']['border_width'])
        elif widget_type == 'CTkCheckBox':
            self.top_geometry.geometry('786x232')
            checkbox_fg_color = self.theme_json_data['CTkCheckbox']['fg_color'][mode]

            checkbox_border_color = self.theme_json_data['CTkCheckbox']['border_color'][mode]

            checkbox_hover_color = self.theme_json_data['CTkCheckbox']['hover_color'][mode]

            checkbox_checkmark_color = self.theme_json_data['CTkCheckbox']['checkmark_color'][mode]

            checkbox_text_color = self.theme_json_data['CTkCheckbox']['text_color'][mode]

            geometry_widget = ctk.CTkCheckBox(master=frm_widget_preview_low,
                                              fg_color=checkbox_fg_color,
                                              border_color=checkbox_border_color,
                                              hover_color=checkbox_hover_color,
                                              checkmark_color=checkbox_checkmark_color,
                                              text_color=checkbox_text_color,
                                              corner_radius=self.theme_json_data['CTkCheckbox']['corner_radius'],
                                              border_width=self.theme_json_data['CTkCheckbox']['border_width'])
        elif widget_type == 'CTkComboBox':
            self.top_geometry.geometry('795x234')

            combobox_fg_color = self.theme_json_data['CTkComboBox']['fg_color'][mode]

            combobox_text_color = self.theme_json_data['CTkComboBox']['text_color'][mode]

            combobox_border_color = self.theme_json_data['CTkComboBox']['border_color'][mode]

            combobox_button_colour = self.theme_json_data[json_widget_type]['button_color'][mode]

            combobox_button_hover_colour = self.theme_json_data[json_widget_type]['button_hover_color'][mode]

            dropdown_fg_colour = self.theme_json_data['DropdownMenu']['fg_color'][mode]

            dropdown_hover_colour = self.theme_json_data['DropdownMenu']['hover_color'][mode]

            dropdown_text_colour = self.theme_json_data['DropdownMenu']['text_color'][mode]

            geometry_widget = ctk.CTkComboBox(master=frm_widget_preview_low,
                                              fg_color=combobox_fg_color,
                                              text_color=combobox_text_color,
                                              border_color=combobox_border_color,
                                              button_color=combobox_button_colour,
                                              button_hover_color=combobox_button_hover_colour,
                                              dropdown_fg_color=dropdown_fg_colour,
                                              dropdown_text_color=dropdown_text_colour,
                                              dropdown_hover_color=dropdown_hover_colour,
                                              corner_radius=self.theme_json_data['CTkCheckbox']['corner_radius'],
                                              border_width=self.theme_json_data['CTkCheckbox']['border_width'],
                                              values=["Option 1", "Option 2", "Option 3", "Option 4..."])
        elif widget_type == 'CTkFrame':
            self.top_geometry.geometry('764x280')
            geometry_widget = ctk.CTkFrame(master=frm_widget_preview_low, fg_color=preview_frame_top,
                                           corner_radius=self.theme_json_data['CTkFrame']['corner_radius'],
                                           border_width=self.theme_json_data['CTkFrame']['border_width'])

            lbl_frame = ctk.CTkLabel(master=geometry_widget, text_color=preview_text_colour, text='CTKFrame')
            lbl_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        elif widget_type == 'CTkLabel':
            self.top_geometry.geometry('755x160')
            geometry_widget = ctk.CTkLabel(master=frm_widget_preview_low,
                                           text_color=preview_text_colour,
                                           fg_color=cbtk.contrast_colour(preview_frame_top, 15),
                                           corner_radius=self.theme_json_data[widget_type]['corner_radius'])
            widget_tooltip = CTkToolTip(geometry_widget, wraplength=200, justify='left',
                                        message='The CTkLabel widget has been intentionally '
                                                'rendered with a contrasting fg_color, so that '
                                                'the corner radius effect may be seen.')
        elif widget_type == 'CTkEntry':
            fg_color = self.theme_json_data['CTkEntry']['fg_color'][mode]
            border_color = self.theme_json_data['CTkEntry']['border_color'][mode]
            self.top_geometry.geometry('754x235')
            geometry_widget = ctk.CTkEntry(master=frm_widget_preview_low,
                                           placeholder_text="CTkEntry",
                                           fg_color=fg_color,
                                           border_color=border_color)

        elif widget_type == 'CTkProgressBar':
            self.top_geometry.geometry('807x225')
            progressbar_fg_color = self.theme_json_data['CTkProgressBar']['fg_color'][mode]

            progressbar_progress_color = self.theme_json_data['CTkProgressBar']['progress_color'][mode]

            progressbar_border_color = self.theme_json_data['CTkProgressBar']['border_color'][mode]
            geometry_widget = ctk.CTkProgressBar(master=frm_widget_preview_low,
                                                 fg_color=progressbar_fg_color,
                                                 progress_color=progressbar_progress_color,
                                                 border_color=progressbar_border_color,
                                                 corner_radius=self.theme_json_data[json_widget_type]
                                                 ['corner_radius'],
                                                 border_width=self.theme_json_data[json_widget_type]
                                                 ['border_width'])
        elif widget_type == 'CTkSlider':
            self.top_geometry.geometry('760x301')
            geometry_widget = ctk.CTkSlider(master=frm_widget_preview_low,
                                            border_width=self.theme_json_data[widget_type]['border_width'])

        elif widget_type == 'CTkOptionMenu':
            self.top_geometry.geometry('806x161')

            optionmenu_fg_colour = self.theme_json_data[json_widget_type]['fg_color'][mode]

            optionmenu_button_colour = self.theme_json_data[json_widget_type]['button_color'][mode]

            optionmenu_button_hover_colour = self.theme_json_data[json_widget_type]['button_hover_color'][mode]

            optionmenu_text_color = self.theme_json_data[json_widget_type]['text_color'][mode]

            dropdown_fg_colour = self.theme_json_data['DropdownMenu']['fg_color'][mode]

            dropdown_hover_colour = self.theme_json_data['DropdownMenu']['hover_color'][mode]

            dropdown_text_colour = self.theme_json_data['DropdownMenu']['text_color'][mode]

            geometry_widget = ctk.CTkOptionMenu(master=frm_widget_preview_low,
                                                fg_color=optionmenu_fg_colour,
                                                text_color=optionmenu_text_color,
                                                button_color=optionmenu_button_colour,
                                                button_hover_color=optionmenu_button_hover_colour,
                                                dropdown_fg_color=dropdown_fg_colour,
                                                dropdown_text_color=dropdown_text_colour,
                                                dropdown_hover_color=dropdown_hover_colour,
                                                corner_radius=self.theme_json_data['CTkOptionMenu']['corner_radius'],
                                                values=["Option 1", "Option 2", "Option 3..."])
            geometry_widget.set("CTkOptionMenu")


        elif widget_type == 'CTkRadioButton':
            self.top_geometry.geometry('800x301')
            radiobutton_fg_color = self.theme_json_data['CTkRadiobutton']['fg_color'][mode]

            radiobutton_border_color = self.theme_json_data['CTkRadiobutton']['border_color'][mode]

            radiobutton_hover_color = self.theme_json_data['CTkRadiobutton']['hover_color'][mode]

            radiobutton_text_color = self.theme_json_data['CTkRadiobutton']['text_color'][mode]

            label_text_colour = self.theme_json_data['CTkLabel']['text_color'][mode]

            geometry_widget = ctk.CTkRadioButton(master=frm_widget_preview_low,
                                                 fg_color=radiobutton_fg_color,
                                                 border_color=radiobutton_border_color,
                                                 hover_color=radiobutton_hover_color,
                                                 text_color=radiobutton_text_color,
                                                 corner_radius=self.theme_json_data[json_widget_type]
                                                 ['corner_radius'],
                                                 border_width_checked=self.theme_json_data[json_widget_type]
                                                 ['border_width_checked'],
                                                 border_width_unchecked=self.theme_json_data[json_widget_type]
                                                 ['border_width_unchecked'])
            lbl_info = ctk.CTkLabel(master=frm_widget_preview_low,
                                    text_color=label_text_colour,
                                    text='Use a right button click, to\nuncheck the radio '
                                         'button.', justify=ctk.CENTER)
            lbl_info.grid(row=0, column=0, padx=50, pady=10)

            geometry_widget.bind("<Button-3>", lambda event, widget=geometry_widget: deselect_widget(widget_id=widget))
        elif widget_type == 'CTkSegmentedButton':
            self.top_geometry.geometry('847x232')
            # CTkTextbox
            seg_fg_color = self.theme_json_data[json_widget_type]['fg_color'][mode]
            print(f'DEBUG: applying colour: {seg_fg_color}')
            seg_selected_color = self.theme_json_data[json_widget_type]['selected_color'][mode]
            seg_selected_hover_color = self.theme_json_data[json_widget_type]['selected_hover_color'][mode]
            seg_unselected_color = self.theme_json_data[json_widget_type]['unselected_color'][mode]
            seg_unselected_hover_color = self.theme_json_data[json_widget_type]['unselected_hover_color'][mode]
            seg_text_color = self.theme_json_data[json_widget_type]['text_color'][mode]
            seg_text_color_disabled = self.theme_json_data[json_widget_type]['text_color_disabled'][mode]

            geometry_widget = ctk.CTkSegmentedButton(master=frm_widget_preview_low,
                                                     fg_color=seg_fg_color,
                                                     selected_color=seg_selected_color,
                                                     selected_hover_color=seg_selected_hover_color,
                                                     unselected_color=seg_unselected_color,
                                                     unselected_hover_color=seg_unselected_hover_color,
                                                     text_color=seg_text_color,
                                                     text_color_disabled=seg_text_color_disabled)
            geometry_widget.grid(row=10, column=0, padx=(15, 0), pady=(30, 0), sticky="nsew", rowspan=1)

            geometry_widget.configure(values=["CTkSegmentedButton", "Value 2", "Value 3"])
            geometry_widget.set("Value 2")

        elif widget_type == 'CTkSwitch':
            self.top_geometry.geometry('766x299')
            switch_fg_colour = self.theme_json_data[json_widget_type]['fg_color'][mode]

            switch_button_colour = self.theme_json_data[json_widget_type]['button_color'][mode]

            switch_button_hover_colour = self.theme_json_data[json_widget_type]['button_hover_color'][mode]

            switch_progress_colour = self.theme_json_data[json_widget_type]['progress_color'][mode]

            switch_text_colour = self.theme_json_data[json_widget_type]['text_color'][mode]

            geometry_widget = ctk.CTkSwitch(master=frm_widget_preview_low,
                                            fg_color=switch_fg_colour,
                                            button_color=switch_button_colour,
                                            text_color=switch_text_colour,
                                            button_hover_color=switch_button_hover_colour,
                                            progress_color=switch_progress_colour,
                                            corner_radius=self.theme_json_data[json_widget_type]['corner_radius'],
                                            border_width=self.theme_json_data[json_widget_type]['border_width']
                                            )
        elif widget_type == 'CTkScrollbar':
            self.top_geometry.geometry('782x267')
            # Harness the scrollbar incorporated
            # to the CTkScrollableFrame widget.
            self.top_geometry.geometry('800x280')
            scrollbar_fg_color = self.theme_json_data[json_widget_type]['fg_color']
            if not isinstance(scrollbar_fg_color, str):
                scrollbar_fg_color = scrollbar_fg_color[cbtk.str_mode_to_int(self.appearance_mode)]
            elif scrollbar_fg_color == "transparent":
                scrollbar_fg_color = self.theme_json_data['CTkFrame']['fg_color'][
                    cbtk.str_mode_to_int(self.appearance_mode)]
            scrollbar_button_color = self.theme_json_data[json_widget_type]['button_color']
            scrollbar_button_hover_color = self.theme_json_data[json_widget_type]['button_hover_color']

            frm_preview = ctk.CTkFrame(frm_widget_preview_low, corner_radius=0)
            frm_preview.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

            # create textbox
            textbox_fg_color = self.theme_json_data['CTkTextbox']['fg_color'][
                cbtk.str_mode_to_int(self.appearance_mode)]
            if not isinstance(textbox_fg_color, str):
                textbox_fg_color = textbox_fg_color[cbtk.str_mode_to_int(self.appearance_mode)]
            textbox_border_color = self.theme_json_data['CTkTextbox']['border_color'][
                cbtk.str_mode_to_int(self.appearance_mode)]
            textbox_text_color = self.theme_json_data['CTkTextbox']['text_color'][
                cbtk.str_mode_to_int(self.appearance_mode)]
            tk_textbox = ctk.CTkTextbox(frm_preview,
                                        activate_scrollbars=False,
                                        fg_color=textbox_fg_color,
                                        border_color=textbox_border_color,
                                        text_color=textbox_text_color,
                                        corner_radius=0)
            tk_textbox.grid(row=0, column=1, sticky="nsew")
            tk_textbox.insert("0.0", text="CTkScrollBar\n\n" + "Bozzy bear woz here...\n\n" * 20)

            # create CTk scrollbar
            geometry_widget = ctk.CTkScrollbar(frm_preview,
                                               command=tk_textbox.yview,
                                               fg_color=scrollbar_fg_color,
                                               button_color=scrollbar_button_color,
                                               button_hover_color=scrollbar_button_hover_color)
            geometry_widget.grid(row=0, column=2, sticky="ns")
            tk_textbox.configure(yscrollcommand=geometry_widget.set)

        elif widget_type == 'CTkTextbox':
            self.top_geometry.geometry('776x243')
            # CTkTextbox
            textbox_fg_color = self.theme_json_data[json_widget_type]['fg_color'][mode]
            if not isinstance(textbox_fg_color, str):
                textbox_fg_color = textbox_fg_color[cbtk.str_mode_to_int(self.appearance_mode)][mode]
            elif textbox_fg_color == "transparent":
                textbox_fg_color = self.theme_json_data['CTkFrame']['fg_color'][mode]
            textbox_border_color = self.theme_json_data[json_widget_type]['border_color'][mode]
            textbox_button_color = self.theme_json_data[json_widget_type]['scrollbar_button_color'][mode]
            textbox_button_hover_color = self.theme_json_data[json_widget_type]['scrollbar_button_hover_color'][mode]
            textbox_text_color = self.theme_json_data[json_widget_type]['text_color'][mode]

            geometry_widget = ctk.CTkTextbox(frm_widget_preview_low,
                                             fg_color=textbox_fg_color,
                                             border_color=textbox_border_color,
                                             scrollbar_button_color=textbox_button_color,
                                             scrollbar_button_hover_color=textbox_button_hover_color,
                                             text_color=textbox_text_color,
                                             width=190,
                                             height=180)
            geometry_widget.grid(row=10, column=0, padx=(15, 0), pady=(30, 0), sticky="nsew", rowspan=1)
            if self.enable_tooltips:
                textbox_tooltip = CTkToolTip(geometry_widget,
                                             wraplength=300,
                                             padding=(5, 5),
                                             x_offset=-100,
                                             justify="left",
                                             message='CTkTextbox')

            geometry_widget.insert("0.0", "CTkTextbox\n\n" + "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, "
                                                             "sed diam nonumy eirmod tempor invidunt ut labore et "
                                                             "dolore magna aliquyam erat, sed diam voluptua.\n\n" * 20)

        else:
            print(f'WARNING: unimplemented widget type: {widget_type}')

        if widget_type not in ['CTkScrollbar']:
            # geometry_widget.grid(row=0, column=0)
            geometry_widget.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        widget_parameter = geometry_parameters_file_json[widget_type]
        slider_dict = {}
        label_dict = {}
        property_value_dict = {}
        row = 0

        for property, parameters in widget_parameter.items():
            lower_value = int(parameters[0])
            upper_value = int(parameters[1])
            label_text = property.replace('_', ' ')
            base_label_text = label_text.replace(widget_type.lower(), '') + ': '
            # This function call is necessary, because there are several naming
            # inconsistencies (at least in CTk 5.1.2), between widget names.
            json_widget_type = mod.json_widget_type(widget_type=widget_type)

            current_value = int(self.theme_json_data[json_widget_type][property])
            label_dict[property] = ctk.CTkLabel(master=frm_controls, text=base_label_text.title() + f'{current_value}')
            label_dict[property].grid(row=row, column=0, sticky='ew', pady=(10, 0))
            row += 1

            slider_dict[property] = ctk.CTkSlider(master=frm_controls,
                                                  from_=lower_value, to=upper_value,
                                                  width=450, number_of_steps=100,
                                                  command=lambda value, label_id=property: slider_callback(label_id,
                                                                                                           value))
            slider_dict[property].grid(row=row, column=0, padx=(25, 25), pady=(0, 15))
            slider_dict[property].set(current_value)
            row += 1

        self.top_geometry.wait_window()

    def close_geometry_dialog(self):
        self.save_widget_geom_geometry()
        self.top_geometry.destroy()

    def save_geometry_edits(self, widget_type):
        for widget_property, property_value in self.geometry_edit_values.items():
            parameters = []
            # This function call is necessary, because there are several naming
            # inconsistencies (at least in CTk 5.1.2), between widget names.
            json_widget_type = mod.json_widget_type(widget_type=widget_type)
            if self.theme_json_data[json_widget_type][widget_property] != property_value:
                self.theme_json_data[json_widget_type][widget_property] = property_value
                self.json_state = 'dirty'

                config_param = widget_property.replace(f'{widget_type.lower()}_', '')
                parameters.append(widget_type)
                parameters.append(config_param)
                parameters.append(str(property_value))
                with open(self.wip_json, "w") as f:
                    json.dump(self.theme_json_data, f, indent=2)
                self.send_command_json(command_type='geometry',
                                       command='update_widget_geometry',
                                       parameters=parameters)

        if self.json_state == 'dirty':
            self.set_option_states()
        self.close_geometry_dialog()

    def set_option_states(self):
        """This function sets the button and menu option states. The states are set based upon a combination of,
        whether a theme is currently selected, and the state of the theme ('dirty'/'clean')"""
        if self.theme:
            tk_state = tk.NORMAL
        else:
            tk_state = tk.DISABLED

        if self.json_state == 'dirty' and self.theme:
            self.file_menu.entryconfig('Reset', state=tk_state)
            self.file_menu.entryconfig('Save', state=tk_state)
            self.btn_reset.configure(state=tk_state)
            self.btn_save.configure(state=tk_state)
        else:
            self.file_menu.entryconfig('Reset', state=tk.DISABLED)
            self.file_menu.entryconfig('Save', state=tk.DISABLED)
            self.btn_reset.configure(state=tk.DISABLED)
            self.btn_save.configure(state=tk.DISABLED)

        # Menu entries
        self.file_menu.entryconfig('Refresh Preview', state=tk_state)
        self.file_menu.entryconfig('Save As', state=tk_state)
        self.file_menu.entryconfig('Delete', state=tk_state)
        self.file_menu.entryconfig('Sync Modes', state=tk_state)
        self.file_menu.entryconfig('Flip Modes', state=tk_state)
        self.file_menu.entryconfig('Sync Palette', state=tk_state)

        if 'provenance' in self.theme_json_data:
            self.file_menu.entryconfig('Provenance', state=tk.NORMAL)
        else:
            self.file_menu.entryconfig('Provenance', state=tk.DISABLED)

        # Non-menu widgets
        self.btn_delete.configure(state=tk_state)
        self.btn_save_as.configure(state=tk_state)
        self.seg_mode.configure(state=tk_state)
        self.opm_properties_filter.configure(state=tk_state)
        self.opm_properties_view.configure(state=tk_state)
        self.swt_render_disabled.configure(state=tk_state)
        self.swt_frame_mode.configure(state=tk_state)
        self.btn_sync_modes.configure(state=tk_state)
        self.btn_sync_palette.configure(state=tk_state)
        self.btn_refresh.configure(state=tk_state)

        if self.harmony_palette_running:
            self.tools_menu.entryconfig('Colour Harmonics', state=tk.DISABLED)
        elif not self.harmony_palette_running and self.theme:
            self.tools_menu.entryconfig('Colour Harmonics', state=tk.NORMAL)

    def save_preferences(self):
        """Save the selected preferences."""
        # Save JSON Directory:
        if self.new_theme_json_dir is not None:
            self.theme_json_dir = self.new_theme_json_dir
            if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='user_preference',
                                               preference_name='theme_json_dir',
                                               preference_value=str(self.theme_json_dir)):
                print(f'Row miss updating preferences theme author.')
            self.json_files = self.user_themes_list()
            self.opm_theme.configure(values=self.json_files)

        preferences_dict = {}
        self.user_name = self.tk_author_name.get()

        if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='user_preference',
                                           preference_name='theme_author', preference_value=self.user_name):
            print(f'Row miss updating preferences theme author.')

        if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='user_preference',
                                           preference_name='control_panel_theme',
                                           preference_value=self.opm_control_panel_theme.get()):
            print(f'Row miss updating preferences control panel theme.')

        control_panel_mode = self.tk_appearance_mode_var.get()
        if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='user_preference',
                                           preference_name='control_panel_mode',
                                           preference_value=control_panel_mode):
            print(f'Row miss updating preferences control panel appearance mode.')

        if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='user_preference',
                                           preference_name='enable_tooltips',
                                           preference_value=self.enable_tooltips):
            print(f'Row miss updating preferences control panel appearance mode.')

        if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='user_preference',
                                           preference_name='last_theme_on_start',
                                           preference_value=self.last_theme_on_start):
            print(f'Row miss updating preferences control panel last theme on start.')

        if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='user_preference',
                                           preference_name='enable_palette_labels',
                                           preference_value=self.enable_palette_labels):
            print(f'Row miss updating preferences: enable palette labels.')

        if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='user_preference',
                                           preference_name='enable_single_click_paste',
                                           preference_value=self.enable_single_click_paste):
            print(f'Row miss updating preferences: enable single click paste.')

        self.shade_adjust_differential = self.opm_shade_adjust_differential.get()
        self.shade_adjust_differential = int(self.shade_adjust_differential)
        if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='user_preference',
                                           preference_name='shade_adjust_differential',
                                           preference_value=self.shade_adjust_differential):
            print(f'Row miss updating preferences: shade adjust differential.')

        self.harmony_contrast_differential = self.opm_harmony_contrast_differential.get()
        self.harmony_contrast_differential = int(self.harmony_contrast_differential)
        if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='user_preference',
                                           preference_name='harmony_contrast_differential',
                                           preference_value=self.harmony_contrast_differential):
            print(f'Row miss updating preferences: harmony contrast differential.')

        ctk.set_appearance_mode(control_panel_mode)
        cbtk.CBtkMenu.update_widgets_mode()
        self.control_panel_mode = control_panel_mode
        self.tk_appearance_mode_var.set(self.control_panel_mode)
        self.status_bar.set_status_text(status_text=f'Preferences saved.')
        self.top_prefs.destroy()

    def switch_preview_appearance_mode(self, event='event'):
        """Actions to choice of preview panel's appearance mode (Light / Dark)"""
        preview_appearance_mode = self.tk_seg_mode.get()
        if preview_appearance_mode == 'Light Mode':
            self.appearance_mode = 'Light'
        else:
            self.appearance_mode = 'Dark'

        if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='auto_save',
                                           preference_name='appearance_mode',
                                           preference_value=self.appearance_mode):
            print(f'Row miss: on update of auto save of selected theme.')

        self.lbl_palette_header.configure(text=f'Theme Palette ({preview_appearance_mode})')

        self.load_theme_palette()
        self.render_widget_properties()

        self.send_command_json(command_type='program',
                               command='set_appearance_mode',
                               parameters=[self.appearance_mode])

        # self.load_theme()

    def render_theme_palette(self):
        render_labels = self.enable_palette_labels
        palette_entries = mod.colour_palette_entries(db_file_path=DB_FILE_PATH)
        menus = []
        self.theme_palette_tiles = []

        preview_appearance_mode = self.tk_seg_mode.get()
        if preview_appearance_mode == 'Light Mode':
            self.appearance_mode = 'Light'
        else:
            self.appearance_mode = 'Dark'
        self.lbl_palette_header = ctk.CTkLabel(master=self.frm_theme_palette,
                                               text=f'Theme Palette ({preview_appearance_mode})',
                                               font=HEADING4)

        self.lbl_palette_header.grid(row=0,
                                     column=0,
                                     sticky='w',
                                     columnspan=12,
                                     pady=(5, 0),
                                     padx=10)

        for tile_dict in palette_entries:
            entry_id = tile_dict['entry_id']
            # Take account of the frame label
            row = int(tile_dict['row']) + 1
            col = int(tile_dict['col'])
            tile_label = tile_dict['label']
            tk_palette_label = tk.StringVar(value=tile_label)
            lbl_tile_label = ctk.CTkLabel(master=self.frm_theme_palette,
                                          textvariable=tk_palette_label,
                                          width=100,
                                          height=15,
                                          font=SMALL_TEXT)
            label_col = col
            if render_labels and row == 1:
                row = 1
                label_row = 2
                lbl_tile_label.grid(row=label_row, column=label_col, padx=0, pady=0)
            elif render_labels and row == 2:
                row = 3
                label_row = 4
                lbl_tile_label.grid(row=label_row, column=label_col, padx=0, pady=0)

            btn_colour_tile = ctk.CTkButton(master=self.frm_theme_palette,
                                            border_width=2,
                                            width=90,
                                            height=40,
                                            corner_radius=10,
                                            text=''
                                            )
            if col == 0:
                padx = (10, 6)
            else:
                padx = 6

            btn_colour_tile.grid(row=row, column=col, padx=padx, pady=0)
            self.theme_palette_tiles.append(btn_colour_tile)
            # colour_tile = self.theme_palette_tiles[entry_id]

            # Add pop-up/context menus to each button...
            context_menu = cbtk.CBtkMenu(btn_colour_tile, tearoff=False)

            context_menu.add_command(label="Copy",
                                     command=lambda button_id=entry_id:
                                     self.copy_palette_colour(palette_button_id=button_id))

            context_menu.add_command(label="Paste",
                                     command=lambda button_id=entry_id:
                                     self.paste_palette_colour(event=None, palette_button_id=button_id))

            context_menu.add_separator()
            shade_down_menu = cbtk.CBtkMenu(context_menu, tearoff=False)
            shade_up_menu = cbtk.CBtkMenu(context_menu, tearoff=False)

            shade_up_menu.add_command(label="Lighter", state="normal",
                                      command=lambda button_id=entry_id, pal_button=btn_colour_tile:
                                      self.lighten_palette_tile(palette_button=pal_button,
                                                                palette_button_id=button_id,
                                                                shade_step=self.shade_adjust_differential,
                                                                multiplier=1))

            shade_up_menu.add_command(label="Lighter x 2", state="normal",
                                      command=lambda button_id=entry_id, pal_button=btn_colour_tile:
                                      self.lighten_palette_tile(palette_button=pal_button,
                                                                palette_button_id=button_id,
                                                                shade_step=self.shade_adjust_differential,
                                                                multiplier=2))

            shade_up_menu.add_command(label="Lighter x 3", state="normal",
                                      command=lambda button_id=entry_id, pal_button=btn_colour_tile:
                                      self.lighten_palette_tile(palette_button=pal_button,
                                                                palette_button_id=button_id,
                                                                shade_step=self.shade_adjust_differential,
                                                                multiplier=3))

            shade_down_menu.add_command(label="Darker", state="normal",
                                        command=lambda button_id=entry_id, pal_button=btn_colour_tile:
                                        self.darken_palette_tile(palette_button=pal_button,
                                                                 palette_button_id=button_id,
                                                                 shade_step=self.shade_adjust_differential,
                                                                 multiplier=1))

            shade_down_menu.add_command(label="Darker x 2", state="normal",
                                        command=lambda button_id=entry_id, pal_button=btn_colour_tile:
                                        self.darken_palette_tile(palette_button=pal_button,
                                                                 palette_button_id=button_id,
                                                                 shade_step=self.shade_adjust_differential,
                                                                 multiplier=2))

            shade_down_menu.add_command(label="Darker x 3", state="normal",
                                        command=lambda button_id=entry_id, pal_button=btn_colour_tile:
                                        self.darken_palette_tile(palette_button=pal_button,
                                                                 palette_button_id=button_id,
                                                                 shade_step=self.shade_adjust_differential,
                                                                 multiplier=3))

            context_menu.add_cascade(label='Lighten shade', menu=shade_up_menu)
            context_menu.add_cascade(label='Darken shade', menu=shade_down_menu)
            context_menu.add_separator()
            context_menu.add_command(label="Colour Picker",
                                     command=lambda button_id=entry_id: self.palette_colour_picker(button_id))
            menus.append(context_menu)

            if self.enable_single_click_paste:
                btn_colour_tile.bind("<Button-1>",
                                     lambda event, button_id=entry_id: self.paste_palette_colour(event,
                                                                                                 button_id))

            btn_colour_tile.bind("<Button-3>",
                                 lambda event, menu=menus[entry_id], button_id=entry_id: self.context_menu(event,
                                                                                                           menu))

    def toggle_frame_mode(self):
        """We need the ability to render the frames in the preview panel as they would appear when we have a top frame
        (a frame whose parent widget is a frame. Conversely, we also need to see how our other widgets render within
        a single frame. This method toggles the preview panel, between the 2 states."""
        if not self.theme:
            return
        frame_mode = self.tk_swt_frame_mode.get()
        if frame_mode == 'top':
            self.send_command_json(command_type='program', command='render_top_frame')
        else:
            self.send_command_json(command_type='program', command='render_base_frame')

    def toggle_render_disabled(self):
        render_state = self.swt_render_disabled.get()
        if render_state:
            self.send_command_json(command_type='program', command='render_preview_disabled')
        else:
            self.send_command_json(command_type='program', command='render_preview_enabled')

    def update_properties_filter(self, view_name):
        """When a different view is selected, we need to update the Properties Filter list accordingly. This method,
        loads the requisite JSON files and derives the new list for us. """
        view_file = str(VIEWS_DIR / view_name) + '.json'
        view_file = Path(view_file)
        self.widget_attributes = mod.json_dict(json_file_path=view_file)
        self.widget_categories = all_widget_categories(self.widget_attributes)
        self.opm_properties_filter.configure(values=self.widget_categories)
        # Cause the Filters to be set to 'All', for the
        # selected view and update the display accordingly.
        self.opm_properties_filter.set('All')
        self.set_filtered_widget_display()
        # self.send_preview_command('Update properties filter...')

    def preferred_json_location(self):
        """A simple method which asks the themes author to navigate to where
         the themes JSON are to be stored/maintained."""
        self.new_theme_json_dir = Path(tk.filedialog.askdirectory(initialdir=self.theme_json_dir))
        self.lbl_pref_theme_dir_disp.configure(text=self.new_theme_json_dir)

    def app_themes_list(self):
        """This method generates a list of theme names, based on the json files found in the application themes folder
         These are basically the theme file names, with the .json extension stripped out."""
        json_files = list(APP_THEMES_DIR.glob('*.json'))
        theme_names = []
        for file in json_files:
            file = os.path.basename(file)
            theme_name = os.path.splitext(file)[0]
            theme_names.append(theme_name)
        theme_names.sort()
        return theme_names

    def user_themes_list(self):
        """This method generates a list of theme names, based on the json files found in the user's themes folder
        (i.e. self.theme_json_dir). These are basically the theme file names, with the .json extension stripped out."""
        json_files = list(self.theme_json_dir.glob('*.json'))
        theme_names = []
        for file in json_files:
            file = os.path.basename(file)
            theme_name = os.path.splitext(file)[0]
            theme_names.append(theme_name)
        theme_names.sort()
        return theme_names

    @staticmethod
    def view_list():
        """This method generates a list of view names, based on the json files found in the assets/views folder.
        These are basically the theme file names, with the .json extension stripped out."""
        json_files = list(VIEWS_DIR.glob('*.json'))
        theme_names = []
        for file in json_files:
            file = os.path.basename(file)
            theme_name = os.path.splitext(file)[0]
            theme_names.append(theme_name)
        theme_names.sort()
        return theme_names

    def load_theme(self, event=None, reload_preview: bool = True):

        if self.json_state == 'dirty':
            confirm = CTkMessagebox(master=self.ctk_control_panel,
                                    title='Confirm Action',
                                    message=f'You have unsaved changes. Are you sure you wish to proceed?',
                                    options=["Yes", "No"])
            response = confirm.get()
            if response == 'No':
                return
        selected_theme = self.opm_theme.get()

        if selected_theme == '-- Select Theme --':
            return

        self.theme_file = selected_theme + '.json'
        self.source_json_file = self.theme_json_dir / self.theme_file
        if not self.source_json_file.exists():
            # Then likely that we are just starting up and last theme
            # opened was probably deleted.
            self.json_files = self.user_themes_list()
            initial_display = self.user_themes_list()
            self.opm_theme.configure(values=initial_display)
            self.opm_theme.set('-- Select Theme --')
            return

        if self.source_json_file:
            self.wip_json = self.TEMP_DIR / self.theme_file
            self.preview_json = self.TEMP_DIR / self.theme_file
            shutil.copyfile(self.source_json_file, self.wip_json)
            self.theme_json_data = mod.json_dict(json_file_path=self.wip_json)

            # self.update_config(section='preferences', option='theme_json_dir', value=self.theme_json_dir)
            self.render_geometry_buttons()
            self.render_theme_palette()
            self.load_theme_palette()
            self.set_filtered_widget_display()

            try:
                self.btn_refresh.configure(state=tk.NORMAL)
            except tk.TclError:
                pass
            self.btn_refresh.configure(state=tk.NORMAL)
            # Enable buttons
            self.seg_mode.configure(state=tk.NORMAL)
            self.opm_properties_filter.configure(state=tk.NORMAL)
            self.btn_save_as.configure(state=tk.NORMAL)
            self.btn_delete.configure(state=tk.NORMAL)
            self.btn_sync_modes.configure(state=tk.NORMAL)
            self.opm_properties_view.configure(state=tk.NORMAL)
            self.swt_render_disabled.configure(state=tk.NORMAL)
            self.file_menu.entryconfig('Save', state=tk.NORMAL)
            self.file_menu.entryconfig('Save As', state=tk.NORMAL)
            self.file_menu.entryconfig('Delete', state=tk.NORMAL)
            self.file_menu.entryconfig('Sync Modes', state=tk.NORMAL)
            self.file_menu.entryconfig('Flip Modes', state=tk.NORMAL)

            self.lbl_title.grid(row=0, column=0, columnspan=2, sticky='ew')
            self.ctk_control_panel.geometry(f'{ControlPanel.PANEL_WIDTH}x{ControlPanel.PANEL_HEIGHT}')
            self.opm_theme.configure(values=self.json_files)
            palette_file = selected_theme + '.json'
            self.theme = selected_theme

            self.json_state = 'clean'
            self.set_option_states()

            palette_file = self.palettes_dir / palette_file
            if not palette_file.exists():
                self.create_theme_palette(selected_theme)

            if reload_preview:
                self.reload_preview()

            # Here we load in the standard CustomTkinter green.json theme. We use this as a reference theme
            # file. This is a belt n' braces approach to ensuring that we aren't missing any widget properties,
            # which may have been introduced, in the event that someone has upgraded to a later version of
            # CustomTkinter to a version that the app has not been updated to deal with. We can't maintain
            # the properties but at least we can update the opened theme, to make the JSON is complete.
            for widget, widget_property in self.reference_theme_json.items():
                if widget not in self.theme_json_data:
                    self.theme_json_data[widget] = widget_property

            # Update the auto-save section of the preferences, to record the last theme we opened.
            # This may be required on the next app startup, if the last_theme_on_start preference is enabled.
            if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='auto_save',
                                               preference_name='selected_theme',
                                               preference_value=selected_theme):
                print(f'Row miss: on update of auto save of selected theme.')
            self.status_bar.set_status_text(status_text_life=30,
                                            status_text=f'Theme file, {self.theme_file}, loaded. ')

    def save_harmonics_geometry(self):
        """Save the harmonics panel geometry to the repo, for the next time the dialog is launched."""
        geometry_row = mod.preference_row(db_file_path=DB_FILE_PATH,
                                          scope='window_geometry',
                                          preference_name='harmonics_panel')
        panel_geometry = self.top_harmony.geometry()
        geometry_row["preference_value"] = panel_geometry
        mod.upsert_preference(db_file_path=DB_FILE_PATH, preference_row_dict=geometry_row)

    def save_widget_geom_geometry(self):
        """Save the widget geometry dialog's geometry to the repo, for the next time the dialog is launched."""
        geometry_row = mod.preference_row(db_file_path=DB_FILE_PATH,
                                          scope='window_geometry',
                                          preference_name='widget_geometry')
        panel_geometry = self.top_geometry.geometry()
        geometry_row["preference_value"] = panel_geometry
        mod.upsert_preference(db_file_path=DB_FILE_PATH, preference_row_dict=geometry_row)

    def on_harmonic_close(self):
        self.rendered_keystone_shades = []
        self.save_harmonics_geometry()
        self.top_harmony.destroy()
        self.harmony_palette_running = False
        self.set_option_states()

    def restore_geom_geometry(self):
        """Restore window geometry of the Widget Geometry dialog from auto-saved preferences"""
        saved_geometry = mod.preference_setting(db_file_path=DB_FILE_PATH,
                                                scope='window_geometry',
                                                preference_name='widget_geometry')
        self.top_geometry.geometry(saved_geometry)
        # self.top_geometry.resizable(False, False)

    def restore_harmony_geometry(self):
        """Restore window geometry from auto-saved preferences"""
        default_geometry = f"{ControlPanel.PANEL_WIDTH}x{ControlPanel.PANEL_HEIGHT}+347+93"
        saved_geometry = mod.preference_setting(db_file_path=DB_FILE_PATH,
                                                scope='window_geometry',
                                                preference_name='harmonics_panel', default=default_geometry)
        self.top_harmony.geometry(saved_geometry)
        self.top_harmony.resizable(False, False)

    def launch_harmony_dialog(self):

        self.HARMONICS_HEIGHT1 = 550
        self.HARMONICS_HEIGHT2 = 550
        self.HARMONICS_HEIGHT3 = 650
        self.rendered_harmony_buttons = []

        self.top_harmony = tk.Toplevel(master=self.ctk_control_panel)
        self.top_harmony.title('Colour Harmonics')

        self.top_harmony.columnconfigure(0, weight=1)
        self.top_harmony.rowconfigure(0, weight=1)
        self.restore_harmony_geometry()

        frm_main = ctk.CTkFrame(master=self.top_harmony, corner_radius=0)
        frm_main.grid(column=0, row=0, sticky='nsew')
        frm_main.columnconfigure(0, weight=1)
        frm_main.rowconfigure(0, weight=1)

        frm_controls = ctk.CTkFrame(master=frm_main)
        frm_controls.grid(column=0, row=0, padx=10, pady=10, sticky='new')

        self.frm_harmony_colours = ctk.CTkFrame(master=frm_main)
        self.frm_harmony_colours.grid(column=0, row=1, padx=10, pady=10, sticky='nsew')

        self.frm_shades_palette = ctk.CTkFrame(master=frm_main)
        self.frm_shades_palette.grid(column=2, row=0, padx=(0, 10), pady=10, sticky='nsew', rowspan=2)

        frm_buttons = ctk.CTkFrame(master=frm_main)
        frm_buttons.grid(column=0, row=2, padx=10, pady=(5, 0), sticky='ew', columnspan=3)

        self.harmony_status_bar = cbtk.CBtkStatusBar(master=self.top_harmony,
                                                     status_text_life=30,
                                                     use_grid=True)

        self.new_theme_json_dir = None

        lbl_keystone_header = ctk.CTkLabel(master=frm_controls,
                                           text=f'Keystone Colour',
                                           font=HEADING4,
                                           justify=tk.CENTER)

        lbl_keystone_header.grid(row=0,
                                 column=0,
                                 sticky='ew',
                                 pady=5,
                                 padx=(25, 25))

        lbl_harmony_header = ctk.CTkLabel(master=self.frm_harmony_colours,
                                          text=f'Colour Harmony',
                                          font=HEADING4,
                                          justify=tk.CENTER)

        lbl_harmony_header.grid(row=0,
                                column=0,
                                sticky='ew',
                                pady=5,
                                padx=(25, 25))

        lbl_keystone_colour = ctk.CTkLabel(master=frm_controls,
                                           text=f'Paste / select color:',
                                           font=REGULAR_TEXT)
        lbl_keystone_colour.grid(row=1,
                                 column=0,
                                 sticky='w',
                                 pady=0,
                                 padx=(25, 0))

        bg_colour = self.theme_json_data.get('provenance', {}).get('keystone colour', None)
        self.btn_keystone_colour = ctk.CTkButton(master=frm_controls,
                                                 border_width=3,
                                                 fg_color=bg_colour,
                                                 width=120,
                                                 height=90,
                                                 corner_radius=15,
                                                 text=''
                                                 )

        self.btn_keystone_colour.grid(row=2, column=0, padx=5, pady=(0, 10))

        self.opm_harmony_method = ctk.CTkOptionMenu(master=frm_controls, values=['Analogous',
                                                                                 'Complementary',
                                                                                 'Split-complementary',
                                                                                 'Triadic',
                                                                                 'Tetradic'],
                                                    command=self.switch_harmony_method)
        self.opm_harmony_method.grid(row=3, column=0, padx=(10, 10), pady=(0, 10))
        harmony_method = self.theme_json_data.get('provenance', {}).get('harmony method', 'Analogous')

        self.opm_harmony_method.set(harmony_method)
        # self.opm_harmony_method.set('Analogous')

        btn_palette_tooltip = cbtk.CBtkToolTip(self.btn_keystone_colour,
                                               text='Right click for options.')
        mnu_keystone = cbtk.CBtkMenu(self.btn_keystone_colour, tearoff=False)
        mnu_keystone.add_command(label="Copy",
                                 command=self.copy_harmony_input_colour)

        mnu_keystone.add_command(label="Paste",
                                 command=self.paste_harmony_keystone_colour)

        mnu_keystone.add_command(label="Colour Picker",
                                 command=self.harmony_input_colour_picker)
        # if self.enable_single_click_paste:
        #    self.btn_keystone_colour.bind("<Button-1>",
        #                     lambda event, button_id=self.paste_harmony_keystone_colour)

        self.btn_keystone_colour.bind("<Button-3>",
                                      lambda event, menu=mnu_keystone: self.context_menu(event, menu))

        if self.theme is not None:
            button_state = ctk.NORMAL
        else:
            button_state = ctk.DISABLED

        btn_close = ctk.CTkButton(master=frm_buttons,
                                  text='Close',
                                  command=self.on_harmonic_close)

        btn_close.grid(row=0, column=0, padx=15, pady=5)

        btn_copy_to_palette = ctk.CTkButton(master=frm_buttons,
                                            text='Copy to Palette',
                                            state=button_state,
                                            command=self.copy_harmonics_to_palette)

        if self.enable_tooltips:
            btn_tooltip = CTkToolTip(btn_copy_to_palette,
                                     wraplength=250,
                                     justify="left",
                                     message='Copy the keystone and harmony colours (not including harmony shades),'
                                             ' to the theme palette scratch slots.')

        btn_copy_to_palette.grid(row=0, column=1, padx=15, pady=5)

        if 'provenance' in self.theme_json_data:
            btn_save_keystone = ctk.CTkButton(master=frm_buttons,
                                              text='Tag Keystone',
                                              state=button_state,
                                              command=self.tag_keystone_colour_to_theme
                                              )
            btn_save_keystone.grid(row=0, column=2, padx=15, pady=5)

            if self.enable_tooltips:
                btn_tooltip = CTkToolTip(btn_save_keystone,
                                         wraplength=250,
                                         justify="left",
                                         x_offset=-50,
                                         message='Tag this keystone colour to the theme.\n\nThis will cause the '
                                                 'keystone colour to be restored when the theme is opened and the '
                                                 'Colour Harmonics dialog opened.')

        harmony_method = self.theme_json_data.get('provenance', {}).get('harmony method', None)
        self.set_harmony_keystone(colour_code=bg_colour, method=harmony_method)
        self.switch_harmony_method()
        self.harmony_palette_running = True
        self.set_option_states()
        self.top_harmony.protocol("WM_DELETE_WINDOW", self.on_harmonic_close)
        self.top_harmony.grab_set()

    def switch_harmony_method(self, event='event'):
        """This method updates the rendered buttons, below the keystone colour button, when we change the harmony
        method (complimentary, triadic etc)."""
        harmony_method = self.opm_harmony_method.get()

        row = 1
        column = 0

        for button in self.rendered_harmony_buttons:
            button.destroy()
            self.rendered_harmony_buttons = []

        harmony_entries = None
        if harmony_method == 'Analogous':
            harmony_entries = 2
        elif harmony_method == 'Complementary':
            harmony_entries = 1
        elif harmony_method == 'Split-complementary':
            harmony_entries = 2
        elif harmony_method == 'Triadic':
            harmony_entries = 2
        elif harmony_method == 'Tetradic':
            harmony_entries = 3
        else:
            print(f'ERROR: Unrecognised harmony colors method: {harmony_method}')

        if harmony_entries == 1:
            self.top_harmony.geometry(f"510x{self.HARMONICS_HEIGHT1}")
        elif harmony_entries == 2:
            self.top_harmony.geometry(f"650x{self.HARMONICS_HEIGHT2}")
        elif harmony_entries == 3:
            self.top_harmony.geometry(f"800x{self.HARMONICS_HEIGHT3}")

        menus = []
        pad_x = (5, 5)
        # Create the buttons for the generated base colours rendered mid to lower left of
        # the colour harmonics dialog.
        for btn_idx in range(harmony_entries):
            btn_palette = ctk.CTkButton(master=self.frm_harmony_colours,
                                        border_width=3,
                                        width=120,
                                        height=90,
                                        corner_radius=15,
                                        text=''
                                        )

            self.rendered_harmony_buttons.append(btn_palette)

            btn_palette_tooltip = cbtk.CBtkToolTip(btn_palette,
                                                   text='Right click for copy option.')

            if row == 0 and harmony_entries > 1:
                pad_y = (0, 0)
            else:
                pad_y = (0, 10)

            btn_palette.grid(row=row, column=column, padx=pad_x, pady=pad_y)

            row += 1

            palette_button = self.rendered_harmony_buttons[btn_idx]
            # Add pop-up/context menus to each button...
            menus.append(cbtk.CBtkMenu(palette_button, tearoff=False))
            menus[btn_idx].config(background=self.ctl_frame_high, foreground=self.ctl_text)
            menus[btn_idx].add_command(label="Copy",
                                       command=lambda button_id=btn_idx:
                                       self.copy_harmony_colour(harmony_button_id=button_id))

            btn_palette.bind("<Button-3>",
                             lambda event, menu=menus[btn_idx], button_id=btn_idx: self.context_menu(event, menu))
        if self.keystone_colour is not None:
            self.populate_harmony_colours()
            self.render_keystone_shades_palette(
                keystone_colour=self.btn_keystone_colour.cget('fg_color'),
                harmony_method=harmony_method)

    def render_keystone_shades_palette(self, keystone_colour: str, harmony_method: str):
        """Render the "shades palette" which displays the keystone colour, the complementary colours,
        and the contrast shades. """

        colour_object = ch.Color(hex_to_rgb(keystone_colour), "", "")

        harmony_entries = 0
        shade_button_rows = 4
        harmony_colours = None
        if harmony_method == 'Analogous':
            harmony_colours = ch.analogousColor(colour_object)
            harmony_entries = 2
        elif harmony_method == 'Complementary':
            harmony_colours = ch.complementaryColor(colour_object)
            harmony_entries = 1
        elif harmony_method == 'Split-complementary':
            harmony_colours = ch.splitComplementaryColor(colour_object)
            harmony_entries = 2
        elif harmony_method == 'Triadic':
            harmony_colours = ch.triadicColor(colour_object)
            harmony_entries = 2
        elif harmony_method == 'Tetradic':
            harmony_colours = ch.tetradicColor(colour_object)
            harmony_entries = 3

        harmony_colours_list = [keystone_colour]
        if harmony_entries == 1:
            colour = tuple(harmony_colours)
            harmony_colour = rgb_to_hex(colour)
            harmony_colours_list.append(harmony_colour)
        else:
            for colour in harmony_colours:
                harmony_colour = rgb_to_hex(tuple(colour))
                harmony_colours_list.append(harmony_colour)

        num_harmony_colours = len(harmony_colours_list)

        harmonic_differential = self.harmony_contrast_differential
        num_shade_buttons = num_harmony_colours * shade_button_rows

        harmony_idx = 0
        contrast_step = 0

        # Create a list of colour shade mappings to assign to the shade buttons that we are about to generate.
        shades_list = []

        for idx in range(num_shade_buttons):
            colour = harmony_colours_list[harmony_idx]
            colour = cbtk.contrast_colour(colour, contrast_step * harmonic_differential)
            shades_list.append(colour)
            if harmony_idx < num_harmony_colours - 1:
                harmony_idx += 1
            else:
                contrast_step += 1
                harmony_idx = 0

        pad_x = 10
        pad_y = 5
        menus = []

        for button in self.rendered_keystone_shades:
            button.destroy()
        self.rendered_keystone_shades = []

        row = 0
        column = 0
        rows_limit = 4
        num_shade_buttons = harmony_entries * 4
        for btn_idx in range(len(shades_list)):
            btn_keystone_shade = ctk.CTkButton(master=self.frm_shades_palette,
                                               fg_color=shades_list[btn_idx],
                                               hover_color=cbtk.contrast_colour(shades_list[btn_idx], 10),
                                               border_width=3,
                                               width=110,
                                               height=100,
                                               corner_radius=10,
                                               text=shades_list[btn_idx]
                                               )

            btn_palette_tooltip = cbtk.CBtkToolTip(btn_keystone_shade,
                                                   text='Right click for copy option.')

            btn_keystone_shade.grid(row=row, column=column, padx=pad_x, pady=pad_y)
            self.rendered_keystone_shades.append(btn_keystone_shade)

            column += 1

            palette_button = self.rendered_keystone_shades[btn_idx]
            menus.append(cbtk.CBtkMenu(palette_button, tearoff=False))
            menus[btn_idx].config(background=self.ctl_frame_high, foreground=self.ctl_text)
            menus[btn_idx].add_command(label="Copy",
                                       command=lambda button_id=btn_idx:
                                       self.copy_keystone_colour(harmony_button_id=button_id))

            btn_keystone_shade.bind("<Button-3>",
                                    lambda event, menu=menus[btn_idx], button_id=btn_idx: self.context_menu(event,
                                                                                                            menu))

            if column > harmony_entries:
                column = 0
                row += 1
                if row == rows_limit:
                    break

    def copy_harmonics_to_palette(self):
        harmonic_differential = self.harmony_contrast_differential
        colour_range = [self.btn_keystone_colour.cget('fg_color')]

        for btn_idx in range(len(self.rendered_harmony_buttons)):
            colour = self.rendered_harmony_buttons[btn_idx].cget('fg_color')
            colour_range.append(colour)
        num_harmony_colours = len(colour_range)

        num_theme_palette_tiles = len(self.theme_palette_tiles)

        harmony_idx = 0
        contrast_step = 0

        num_tiles = ControlPanel.THEME_PALETTE_TILES
        num_rows = ControlPanel.THEME_PALETTE_ROWS

        for idx in range(num_harmony_colours):

            colour = colour_range[harmony_idx]
            colour = cbtk.contrast_colour(colour, contrast_step * harmonic_differential)
            # We want to copy the gemerated colours to the "scratch" tile locations. These are
            # the 1st two tiles (actually buttons) on each of the two palette rows, so...

            self.set_palette_colour(palette_button_id=idx, colour=colour)

            if harmony_idx < num_harmony_colours - 1:
                harmony_idx += 1
            else:
                contrast_step += 1
                harmony_idx = 0

        self.harmony_status_bar.set_status_text(
            status_text=f'Keystone and generated colours copied to palette.')

        self.theme_json_data['provenance']['keystone colour'] = colour_range[0]

        harmony_method = self.opm_harmony_method.get()
        self.theme_json_data['provenance']['harmony method'] = harmony_method

        self.json_state = 'dirty'
        self.set_option_states()

    def tag_keystone_colour_to_theme(self):
        keystone_colour = self.btn_keystone_colour.cget('fg_color')
        harmony_method = self.opm_harmony_method.get()
        self.theme_json_data['provenance']['keystone colour'] = keystone_colour
        self.theme_json_data['provenance']['harmony method'] = harmony_method
        self.theme_json_data['provenance']['harmony differential'] = self.harmony_contrast_differential
        self.json_state = 'dirty'
        self.set_option_states()
        self.harmony_status_bar.set_status_text(
            status_text=f'Keystone colour tagged to theme {self.theme}.')

    def lighten_palette_tile(self, palette_button: ctk.CTkButton,
                             palette_button_id: int,
                             shade_step: int,
                             multiplier: int = 1):
        self.set_option_states()
        widget_colour = palette_button.cget('fg_color')
        lighter_shade = cbtk.shade_up(color=widget_colour, differential=shade_step, multiplier=multiplier)
        palette_button.configure(fg_color=lighter_shade)
        if self.appearance_mode == 'Light':
            mode_idx = 0
        else:
            mode_idx = 1
        if lighter_shade != widget_colour:
            pyperclip.copy(lighter_shade)
            # Leverage the _paste_palette_colour method to update the widget and the preview panel.
            self.paste_palette_colour(event=None, palette_button_id=palette_button_id)

    def darken_palette_tile(self, palette_button: ctk.CTkButton,
                            palette_button_id: int,
                            shade_step: int,
                            multiplier: int = 1):
        self.set_option_states()
        widget_colour = palette_button.cget('fg_color')
        darker_shade = cbtk.shade_down(color=widget_colour, differential=shade_step, multiplier=multiplier)
        palette_button.configure(fg_color=darker_shade)
        if self.appearance_mode == 'Light':
            mode_idx = 0
        else:
            mode_idx = 1
        if darker_shade != widget_colour:
            pyperclip.copy(darker_shade)
            # Leverage the _paste_palette_colour method to update the widget and the preview panel.
            self.paste_palette_colour(event=None, palette_button_id=palette_button_id)

    def lighten_widget_property_shade(self, property_widget: ctk.CTkButton,
                                      widget_property: str,
                                      shade_step: int,
                                      multiplier: int = 1):
        """Lighten the specified widget property shade, by a specified shade_step, optionally multiplied by a
        coefficient (multiplier)."""
        self.set_option_states()
        widget_colour = property_widget.cget('fg_color')

        lighter_shade = cbtk.shade_up(color=widget_colour, differential=shade_step, multiplier=multiplier)
        property_widget.configure(fg_color=lighter_shade)
        if self.appearance_mode == 'Light':
            mode_idx = 0
        else:
            mode_idx = 1
        if lighter_shade != widget_colour:
            pyperclip.copy(lighter_shade)
            # Leverage the _paste_color method to update the widget and the preview panel.
            self.paste_colour(event=None, widget_property=widget_property)

    def darken_widget_property_shade(self, property_widget: ctk.CTkButton,
                                     widget_property: str,
                                     shade_step: int,
                                     multiplier: int = 1):
        """Darken the specified widget property shade, by a specified shade_step, optionally multiplied by a
        coefficient (multiplier)."""
        self.set_option_states()
        widget_colour = property_widget.cget('fg_color')

        darker_shade = cbtk.shade_down(color=widget_colour, differential=shade_step, multiplier=multiplier)
        print(f'Incoming shade: {widget_colour} / Darker shade: {darker_shade}')
        property_widget.configure(fg_color=darker_shade)
        if self.appearance_mode == 'Light':
            mode_idx = 0
        else:
            mode_idx = 1
        if darker_shade != widget_colour:
            pyperclip.copy(darker_shade)
            # Leverage the _paste_color method to update the widget and the preview panel.
            self.paste_colour(event=None, widget_property=widget_property)

    def copy_harmony_input_colour(self, event=None, shade_copy=False):
        colour = self.btn_keystone_colour.cget('fg_color')
        if shade_copy:
            colour = cbtk.contrast_colour(colour, self.shade_adjust_differential)
        pyperclip.copy(colour)
        self.harmony_status_bar.set_status_text(
            status_text=f'Colour {colour} copied to clipboard.')

    def paste_harmony_keystone_colour(self):
        """Paste the colour currently stored in the paste buffer, to the harmony input button."""
        new_colour = pyperclip.paste()
        if not cbtk.valid_colour(new_colour):
            self.harmony_status_bar.set_status_text(status_text='Attempted paste of non colour code text - ignored.')
            return
        harmony_method = self.opm_harmony_method.get()
        self.set_harmony_keystone(colour_code=new_colour, method=harmony_method)
        self.populate_harmony_colours()
        self.harmony_status_bar.set_status_text(
            status_text=f'Colour {new_colour} assigned.')

    def set_harmony_keystone(self, colour_code: str, method: str):
        hover_colour = cbtk.contrast_colour(colour_code)
        if colour_code:
            self.btn_keystone_colour.configure(fg_color=colour_code,
                                               hover_color=hover_colour)

        if method:
            # set the harmony method, as tagged in the theme file.
            self.opm_harmony_method.set(method)
            self.keystone_colour = colour_code

    def copy_keystone_colour(self, event=None, harmony_button_id=None, shade_copy=False):
        colour = self.rendered_keystone_shades[harmony_button_id].cget('fg_color')
        if shade_copy:
            colour = cbtk.contrast_colour(colour, self.shade_adjust_differential)
        pyperclip.copy(colour)
        self.harmony_status_bar.set_status_text(
            status_text=f'Colour {colour} copied from palette entry {harmony_button_id + 1} to clipboard.')

    def copy_harmony_colour(self, event=None, harmony_button_id=None, shade_copy=False):
        colour = self.rendered_harmony_buttons[harmony_button_id].cget('fg_color')
        if shade_copy:
            colour = cbtk.contrast_colour(colour, self.shade_adjust_differential)
        if shade_copy:
            colour = cbtk.contrast_colour(colour, self.shade_adjust_differential)
        pyperclip.copy(colour)

        self.harmony_status_bar.set_status_text(
            status_text=f'Colour {colour} copied from palette entry {harmony_button_id + 1} to clipboard.')

    def harmony_input_colour_picker(self):
        # self.harmonics_label_count
        primary_colour = askcolor(master=self.top_harmony,
                                  initialcolor=self.keystone_colour,
                                  title=f'Harmony Source Colour Selection')

        if primary_colour[1] is not None:
            primary_colour = primary_colour[1]
            self.btn_keystone_colour.configure(fg_color=primary_colour,
                                               hover_color=primary_colour)
            self.status_bar.set_status_text(
                status_text=f'Colour {primary_colour} assigned.')
            self.keystone_colour = primary_colour
            self.populate_harmony_colours()

    def harmony_colour_picker(self, palette_button_id):
        # self.harmonics_label_count
        primary_colour = askcolor(master=self.top_harmony,
                                  title=f'Harmony Source Colour Selection')

        if primary_colour[1] is not None:
            primary_colour = primary_colour[1]
            self.rendered_harmony_buttons[0].configure(fg_color=primary_colour,
                                                       hover_color=primary_colour)
            self.status_bar.set_status_text(
                status_text=f'Colour {primary_colour} assigned to palette entry {palette_button_id + 1}.')
            self.keystone_colour = primary_colour
        self.populate_harmony_colours()

    def populate_harmony_colours(self):
        primary_colour = self.keystone_colour
        harmony_method = self.opm_harmony_method.get()
        colour_object = ch.Color(hex_to_rgb(self.keystone_colour), "", "")

        harmony_entries = 0
        harmony_colours = None
        if harmony_method == 'Analogous':
            harmony_colours = ch.analogousColor(colour_object)
            harmony_entries = 2
        elif harmony_method == 'Complementary':
            harmony_colours = ch.complementaryColor(colour_object)
            harmony_entries = 1
        elif harmony_method == 'Split-complementary':
            harmony_colours = ch.splitComplementaryColor(colour_object)
            harmony_entries = 2
        elif harmony_method == 'Triadic':
            harmony_colours = ch.triadicColor(colour_object)
            harmony_entries = 2
        elif harmony_method == 'Tetradic':
            harmony_colours = ch.tetradicColor(colour_object)
            harmony_entries = 3
        elif harmony_method == 'Monochromatic':
            harmony_colours = ch.monochromaticColor(colour_object)
            harmony_entries = 9

        for btn_idx in range(harmony_entries):
            if harmony_entries == 1:
                colour = harmony_colours
            else:
                colour = harmony_colours[btn_idx]
            harmony_colour = rgb_to_hex(colour)
            self.rendered_harmony_buttons[btn_idx].configure(fg_color=harmony_colour,
                                                             hover_color=harmony_colour)
        self.render_keystone_shades_palette(keystone_colour=primary_colour, harmony_method=harmony_method)

    def load_theme_palette(self, theme_name=None):
        """Determine and open the JSON theme palette file, for the selected theme, and marry the colours mapped in
        the file, to the palette widgets. """
        if theme_name is None:
            theme_name = self.theme_file
        palette_json = theme_name
        self.palette_file = self.palettes_dir / palette_json
        if not self.palette_file.exists():
            self.create_theme_palette(theme_name)

        self.theme_palette = mod.json_dict(json_file_path=self.palette_file)

        mode = cbtk.str_mode_to_int(self.appearance_mode)

        # Marry the palette buttons to their palette colours
        try:
            for entry_id, button in enumerate(self.theme_palette_tiles):
                colour = self.theme_palette[str(entry_id)][mode]
                hover_colour = cbtk.contrast_colour(colour)
                # button.configure(fg_color=colour, hover_color=hover_colour)
                button.configure(fg_color=colour, hover_color=hover_colour)
        except IndexError:
            pass

    def reset_theme(self):
        """Reset the theme file, to the state of the last save operation, or the state when it was opened,
        if there has been no intervening save. """
        confirm = CTkMessagebox(master=self.ctk_control_panel,
                                title='Confirm Action',
                                message=f'You have unsaved changes. Are you sure you wish to discard them?',
                                options=["Yes", "No"])
        if confirm.get() == 'No':
            return
        self.json_state = 'clean'
        # TODO: Remove this line below
        # self.load_theme_palette()
        self.load_theme()

    def create_theme(self):
        """Create a new theme. This is based on the default.json file."""
        if self.json_state == 'dirty':
            confirm = CTkMessagebox(master=self.ctk_control_panel,
                                    title='Confirm Action',
                                    message=f'You have unsaved changes. Are you sure you wish to discard them?',
                                    options=["Yes", "No"])
            if confirm.get() == 'No':
                return
        source_file = ETC_DIR / 'default.json'
        dialog = ctk.CTkInputDialog(text="Enter new theme name:", title="Create New Theme")
        new_theme = dialog.get_input()
        if new_theme:
            if not valid_theme_name(new_theme):
                self.status_bar.set_status_text(
                    status_text=f'The entered theme name contains disallowed characters - allowed: alphanumeric, '
                                f'underscores & ()')
                return
            # If user has included a ".json" extension, remove it, because we add one below.
            new_theme_basename = os.path.splitext(new_theme)[0]
            new_theme = new_theme_basename + '.json'
            new_theme_path = self.theme_json_dir / new_theme
            if new_theme_path.exists():
                self.status_bar.set_status_text(status_text=f'Theme {new_theme} already exists - '
                                                            f'please choose another name!')
                return
            shutil.copyfile(source_file, new_theme_path)
            self.json_files = self.user_themes_list()
            self.opm_theme.configure(values=self.json_files)
            self.opm_theme.set(new_theme_basename)
            self.load_theme(reload_preview=False)
            self.theme_json_data['provenance']['theme name'] = new_theme_basename
            self.theme_json_data['provenance']['created with'] = f"CTk Theme Builder v{__version__}"
            # current dateTime
            now = datetime.now()
            # convert to string
            date_created = now.strftime("%b %d %Y %H:%M:%S")
            self.theme_json_data['provenance']['date created'] = date_created
            if self.theme_author:
                self.theme_json_data['provenance']['theme author'] = self.theme_author
            else:
                self.theme_json_data['provenance']['theme author'] = 'Unknown'
            self.save_theme()
            self.status_bar.set_status_text(status_text=f'New theme {new_theme} created.')
            self.reload_preview()

    def delete_theme(self):
        """Delete the currently selected theme."""
        confirm = CTkMessagebox(master=self.ctk_control_panel,
                                title='Confirm Action',
                                message=f'All data, for theme "{self.theme}", will be '
                                        f'purged. Are you sure you wish to continue?',
                                options=["Yes", "No"])
        if confirm.get() == 'No':
            self.seg_mode.set(self.appearance_mode)
            return

        os.remove(self.source_json_file)
        source_palette_file = self.theme + '.json'
        source_palette_path = self.palettes_dir / source_palette_file
        if source_palette_path.exists():
            os.remove(source_palette_path)

        self.json_files = self.user_themes_list()
        initial_display = self.user_themes_list()
        initial_display.insert(0, '-- Select Theme --')
        self.opm_theme.configure(values=initial_display)
        self.opm_theme.set('-- Select Theme --')
        self.seg_mode.configure(state=tk.DISABLED)
        self.opm_properties_filter.configure(state=tk.DISABLED)
        self.btn_save_as.configure(state=tk.DISABLED)
        self.btn_delete.configure(state=tk.DISABLED)
        self.btn_sync_modes.configure(state=tk.DISABLED)
        self.opm_properties_view.configure(state=tk.DISABLED)
        self.swt_render_disabled.configure(state=tk.DISABLED)
        self.btn_reset.configure(state=tk.DISABLED)
        self.btn_save.configure(state=tk.DISABLED)
        self.status_bar.set_status_text(status_text_life=30,
                                        status_text=f'Theme, "{self.theme}", has been deleted. ')
        self.json_state = 'clean'

    def save_theme_as(self):
        """Save's the currently selected theme to a new theme. If the current theme has been modified, the modified
        state is saved. The new "save as" theme, becomes the current theme. This operation, also duplicates the
        palette file, to the new theme. """
        # current dateTime

        source_file = self.source_json_file
        dialog = ctk.CTkInputDialog(text="Enter new theme name:", title="Create New Theme")
        new_theme = dialog.get_input()
        if new_theme:
            if not valid_theme_name(new_theme):
                self.status_bar.set_status_text(status_text=f'The entered theme name contains prohibited characters '
                                                            f'- allowed: alphanumeric, underscores & ()')
                return
            new_theme = os.path.splitext(new_theme)[0]
            now = datetime.now()
            # convert to string
            date_saved_as = now.strftime("%b %d %Y %H:%M:%S")

            if self.theme_author:
                theme_author = self.theme_author
            else:
                theme_author = 'Unknown'

            if 'provenance' in self.theme_json_data:
                self.theme_json_data['provenance']['theme name'] = new_theme
                self.theme_json_data['provenance']['date created'] = date_saved_as
                self.theme_json_data['provenance']['last modified'] = date_saved_as
                self.theme_json_data['provenance']['theme author'] = theme_author
                self.theme_json_data['provenance']['last modified by'] = theme_author
                self.theme_json_data['provenance']['created with'] = f"CTk Theme Builder v{__version__}"
            else:
                provenance = {"theme name": new_theme,
                              "theme author": theme_author,
                              "date created": date_saved_as,
                              "last modified by": theme_author,
                              "last modified": "Apr 26 2023 14:40:22",
                              "created with": f"CTk Theme Builder v{__version__}",
                              "keystone colour": None,
                              "harmony method": None,
                              "harmony differential": None}
                self.theme_json_data['provenance'] = provenance

            # If user has included a ".json" extension, remove it, because we add one below.
            self.theme_file = new_theme + '.json'
            # Set the theme source file to the new path, so that when we call save_theme(),
            # it dumps the current WIP to the new theme file.
            self.source_json_file = self.theme_json_dir / self.theme_file

            self.opm_theme.configure(command=None)
            self.opm_theme.set(new_theme)
            self.opm_theme.configure(command=self.load_theme)
            new_theme_json_file = new_theme + '.json'
            new_theme_path = self.theme_json_dir / new_theme_json_file
            shutil.copyfile(source_file, new_theme_path)

            new_palette_path = self.palettes_dir / new_theme_json_file
            source_palette_file = self.theme + '.json'
            source_palette_path = self.palette_file
            shutil.copyfile(source_palette_path, new_palette_path)
            self.palette_file = new_palette_path
            self.save_theme()
            self.json_files = self.user_themes_list()
            self.opm_theme.configure(values=self.json_files)
            self.theme = new_theme

    def paste_colour(self, event, widget_property):
        """Paste the colour currently stored in the paste buffer, to the selected button, where the paste operation
        was invoked."""
        new_colour = pyperclip.paste()
        if not cbtk.valid_colour(new_colour):
            self.status_bar.set_status_text(status_text='Attempted paste of non colour code text - ignored.')
            return
        self.set_widget_colour(widget_property=widget_property, new_colour=new_colour)
        hover_colour = cbtk.contrast_colour(new_colour)
        self.widgets[widget_property]['button'].configure(fg_color=new_colour, hover_color=hover_colour)
        self.status_bar.set_status_text(
            status_text=f'Colour {new_colour} assigned to widget property {widget_property}.')
        widget_type, base_property = mod.widget_property_split(widget_property=widget_property)
        self.json_state = 'dirty'
        self.set_option_states()

    def paste_palette_colour(self, event, palette_button_id):
        new_colour = pyperclip.paste()
        if not cbtk.valid_colour(new_colour):
            self.status_bar.set_status_text(status_text='Attempted paste of non colour code - pasted text ignored.')
            return
        self.set_palette_colour(palette_button_id=palette_button_id, colour=new_colour)
        self.status_bar.set_status_text(
            status_text=f'Colour {new_colour} assigned to palette entry {palette_button_id + 1}.')

    def set_palette_colour(self, palette_button_id, colour):
        hover_colour = cbtk.contrast_colour(colour)
        self.theme_palette_tiles[palette_button_id].configure(fg_color=colour, hover_color=hover_colour)
        self.json_state = 'dirty'
        self.set_option_states()

    def set_filtered_widget_display(self, dummy='dummy'):
        properties_filter = self.opm_properties_filter.get()
        if properties_filter == 'All':
            self.ctk_control_panel.geometry(f'{ControlPanel.PANEL_WIDTH}x{ControlPanel.PANEL_HEIGHT}')
        else:
            self.ctk_control_panel.geometry(f'{ControlPanel.PANEL_WIDTH}x{ControlPanel.PANEL_HEIGHT}')
        self.render_widget_properties()

    def property_colour_picker(self, event, widget_property):
        prev_colour = self.widgets[widget_property]["colour"]
        new_colour = askcolor(master=self.ctk_control_panel, title='Pick colour for : ' + widget_property,
                              initialcolor=prev_colour)
        if new_colour[1] is not None:
            new_colour = new_colour[1]
            self.set_widget_colour(widget_property=widget_property, new_colour=new_colour)

    def palette_colour_picker(self, palette_button_id):
        prev_colour = self.theme_palette_tiles[palette_button_id].cget('fg_color')
        new_colour = askcolor(master=self.frm_theme_palette,
                              title=f'Pick colour for palette entry number {palette_button_id + 1}',
                              initialcolor=prev_colour)

        if new_colour[1] is not None:
            new_colour = new_colour[1]
            self.theme_palette_tiles[palette_button_id].configure(fg_color=new_colour, hover_color=new_colour)
            self.status_bar.set_status_text(
                status_text=f'Colour {new_colour} assigned to palette entry {palette_button_id + 1}.')
            self.json_state = 'dirty'
            self.set_option_states()

    @staticmethod
    def context_menu(event: tk.Event = None, menu: cbtk.CBtkMenu = None):
        menu.tk_popup(event.x_root, event.y_root)

    def copy_palette_colour(self, event=None, palette_button_id=None, shade_copy=False):
        colour = self.theme_palette_tiles[palette_button_id].cget('fg_color')
        if shade_copy:
            colour = cbtk.contrast_colour(colour, self.shade_adjust_differential)
        pyperclip.copy(colour)
        self.status_bar.set_status_text(
            status_text=f'Colour {colour} copied from palette entry {palette_button_id + 1} to clipboard.')

    def render_widget_properties(self, dummy=None):
        """Here we render the widget properties, within the control panel, along with their colour settings."""
        filter_key = self.opm_properties_filter.get()
        self.filter_list = self.widget_attributes[filter_key]
        # self.appearance_mode = self.seg_mode.get()

        widget_frame = self.frm_colour_edit_widgets
        colours = mod.colour_dictionary(self.wip_json)

        view_selection = self.opm_properties_view.get()
        filter_selection = self.opm_properties_filter.get()

        view = f'{view_selection} / {filter_selection}'

        # If this is not the first load, destroy
        # our label and re-create.
        try:
            self.lbl_header.destroy()
        except AttributeError:
            pass

        self.lbl_header = ctk.CTkLabel(master=widget_frame,
                                       text=f' Colour Mappings: {view}',
                                       font=HEADING3)

        self.lbl_header.grid(row=0,
                             column=0,
                             sticky='w',
                             columnspan=12,
                             pady=(5, 0),
                             padx=0)

        sorted_widget_properties = sorted(colours.items(), key=operator.itemgetter(0))
        row = 1
        # The offset is used to control the column we place the widget details in.
        # We aim to stack them into 3 columns.

        for entry in self.widgets.values():
            btn_property = entry['button']
            lbl_property = entry['label']
            try:
                btn_property.destroy()
                lbl_property.destroy()
            except ValueError:
                pass

        appearance_mode_index = cbtk.str_mode_to_int(self.appearance_mode)
        menus = []
        btn_idx = 0
        pad_x = 5
        pad_y = 5

        # Build a dictionary of our rendered properties/values.
        rendered_widgets = {}
        for entry in sorted_widget_properties:
            property_id = entry[0]
            property_value = entry[1]
            rendered_widgets[property_id] = property_value
        # Use a Python generator function to yield successive widgets from the list.
        member_gen = mod.widget_member(widget_entries=rendered_widgets, filter_list=self.filter_list)
        for row in range(1, 30):
            for column_base in range(0, 3):
                column = column_base * 2
                try:
                    key = next(member_gen)
                    widget_type, widget_property = mod.widget_property_split(key)
                    json_widget_type = mod.json_widget_type(widget_type=widget_type)
                    colour_value = self.theme_json_data[json_widget_type][widget_property]
                except StopIteration:
                    break

                if colour_value == "transparent":
                    colour = None
                else:
                    colour = colour_value[appearance_mode_index]

                label = key.replace('_', ' ')
                hover_colour = cbtk.contrast_colour(colour, 30)
                btn_property = ctk.CTkButton(master=widget_frame,
                                             fg_color=colour,
                                             hover_color=hover_colour,
                                             border_width=2,
                                             width=30,
                                             height=30,
                                             text='')
                btn_property.grid(row=row, column=column + 1, padx=pad_x, pady=pad_y)

                lbl_property = ctk.CTkLabel(master=widget_frame, text=' ' + label, anchor='e')
                lbl_property.grid(row=row, column=column + 2, sticky='w', pady=pad_y)

                # Our widget dictionary helps us keep track of the state of the rendered widgets.
                # This is required, for example, if we switch between Light and Dark mode, make some
                # changes, and then switch back again. In which case, we need to determine which
                # widgets are dirty (updated) and send appropriate messages to ensure the colours
                # get updated to the preview display. In this case we need to get  the actual colour
                # from the theme JSON, since that stores both Light and Dark mode colours.
                self.widgets[key] = {"widget": btn_property, "button": btn_property, "colour": colour,
                                     'label': lbl_property, "light_status": 'clean', "dark_status": 'clean'}
                # Set a binding so that we can paste a colour, previously copied into our clipboard
                if self.enable_single_click_paste and colour_value != "transparent":
                    self.widgets[key]['widget'].bind("<Button-1>",
                                                     lambda event, wgt_property=key: self.paste_colour(event,
                                                                                                       wgt_property))
                if self.enable_tooltips:
                    if colour_value != 'transparent':
                        btn_tooltip = cbtk.CBtkToolTip(btn_property,
                                                       text='Right click for colour & clipboard functions.')
                    else:
                        btn_tooltip = cbtk.CBtkToolTip(btn_property,
                                                       text='Colour set to "transparent" - context menu disabled.')

                if colour_value != "transparent":
                    # Add pop-up/context menus to each property button.
                    context_menu = cbtk.CBtkMenu(self.widgets[key]['widget'], tearoff=False)
                    # menus.append(main_menu)
                    context_menu.add_command(label="Copy",
                                             command=lambda wgt_property=key:
                                             self.copy_property_colour(event=None, widget_property=wgt_property))

                    context_menu.add_command(label="Paste",
                                             command=lambda wgt_property=key:
                                             self.paste_colour(event=None, widget_property=wgt_property))
                    context_menu.add_separator()
                    shade_up_menu = cbtk.CBtkMenu(context_menu, tearoff=False)
                    shade_up_menu.add_command(label="Lighter", state="normal",
                                              command=lambda widget=btn_property, wgt_type=json_widget_type,
                                                             wgt_property=key:
                                              self.lighten_widget_property_shade(property_widget=widget,
                                                                                 widget_property=wgt_property,
                                                                                 shade_step=self.shade_adjust_differential,
                                                                                 multiplier=1))

                    shade_up_menu.add_command(label="Lighter x 2", state="normal",
                                              command=lambda widget=btn_property, wgt_type=json_widget_type,
                                                             wgt_property=key:
                                              self.lighten_widget_property_shade(property_widget=widget,
                                                                                 widget_property=wgt_property,
                                                                                 shade_step=self.shade_adjust_differential,
                                                                                 multiplier=2))

                    shade_up_menu.add_command(label="Lighter x 3", state="normal",
                                              command=lambda widget=btn_property, wgt_type=json_widget_type,
                                                             wgt_property=key:
                                              self.lighten_widget_property_shade(property_widget=widget,
                                                                                 widget_property=wgt_property,
                                                                                 shade_step=self.shade_adjust_differential,
                                                                                 multiplier=3))

                    shade_down_menu = cbtk.CBtkMenu(context_menu, tearoff=False)
                    shade_down_menu.add_command(label="Darker", state="normal",
                                                command=lambda widget=btn_property, wgt_type=json_widget_type,
                                                               wgt_property=key:
                                                self.darken_widget_property_shade(property_widget=widget,
                                                                                  widget_property=wgt_property,
                                                                                  shade_step=self.shade_adjust_differential,
                                                                                  multiplier=1))

                    shade_down_menu.add_command(label="Darker x 2", state="normal",
                                                command=lambda widget=btn_property, wgt_type=json_widget_type,
                                                               wgt_property=key:
                                                self.darken_widget_property_shade(property_widget=widget,
                                                                                  widget_property=wgt_property,
                                                                                  shade_step=self.shade_adjust_differential,
                                                                                  multiplier=2))

                    shade_down_menu.add_command(label="Darker x 3", state="normal",
                                                command=lambda widget=btn_property, wgt_type=json_widget_type,
                                                               wgt_property=key:
                                                self.darken_widget_property_shade(property_widget=widget,
                                                                                  widget_property=wgt_property,
                                                                                  shade_step=self.shade_adjust_differential,
                                                                                  multiplier=3))

                    context_menu.add_cascade(label='Lighter shade', menu=shade_up_menu)
                    context_menu.add_cascade(label='Darker shade', menu=shade_down_menu)
                    context_menu.add_separator()
                    context_menu.add_command(label="Colour Picker",
                                             command=lambda wgt_property=key:
                                             self.property_colour_picker(event=None,
                                                                         widget_property=wgt_property))
                    self.widgets[key]['widget'].bind("<Button-3>",
                                                     lambda event, menu=context_menu, button_id=btn_idx:
                                                     self.context_menu(event, menu))

                    btn_idx += 1

    def sync_appearance_mode(self):
        """This method allows us to copy our Dark configuration (if Sark is our current selection, to our Light and
        vice-versa """
        current_mode = self.seg_mode.get()

        if current_mode.lower() == 'light mode':
            to_mode_description = 'Dark'
            to_mode = 1
        else:
            to_mode_description = 'Light'
            to_mode = 0

        confirm = CTkMessagebox(master=self.ctk_control_panel,
                                title='Confirm Action',
                                message=f'This will replace the theme\'s "{to_mode_description}" mode settings with '
                                        f'those from the "{current_mode}" configuration.',
                                options=["Yes", "No"])
        if confirm.get() == 'Cancel':
            return
        counter = 0
        for property_id in self.filter_list:
            widget_type, widget_property = mod.widget_property_split(property_id)
            json_widget_type = mod.json_widget_type(widget_type=widget_type)
            if str(self.theme_json_data[json_widget_type][widget_property]) == "transparent":
                continue
            try:
                self.theme_json_data[json_widget_type][widget_property][to_mode] = self.widgets[property_id]["colour"]
                counter += 1
            except TypeError:
                print(f"TypeError on: {widget_type} / {widget_property}")
                print(f"             Current setting: {str(self.theme_json_data[widget_type][widget_property])}")
                print(f"             Attempt setting: {str(self.widgets[property_id]['colour'])}")
                raise
            except KeyError:
                print(f"KeyError on: {widget_type} / {widget_property}")
                print(f"             Current setting: {str(self.theme_json_data[widget_type][widget_property])}")
                print(f"             Attempt setting: {str(self.widgets[property_id]['colour'])}")
                raise
        print(f'{counter} properties synchronised.')
        self.json_state = 'dirty'
        self.set_option_states()
        self.reload_preview()

    def sync_theme_palette(self):
        """Sync the theme palette for the current appearance mode to its counter-part."""
        current_mode = self.seg_mode.get()
        if current_mode.lower() == 'light':
            to_mode_description = 'Dark'
            from_mode = 0
            to_mode = 1
            message = "Palette sync: Appearance mode, 'Light', copied to 'Dark. Changes will take " \
                      "effect on save / reopen."
        else:
            to_mode_description = 'Light'
            from_mode = 1
            to_mode = 0
            message = "Palette sync: Appearance mode, 'Dark', copied to 'Light'. Changes will take " \
                      "effect on save / reopen."

        confirm = CTkMessagebox(master=self.ctk_control_panel,
                                title='Confirm Action',
                                message=f'This will replace and save the Theme Palette colours for the theme\'s '
                                        f'"{to_mode_description}" mode settings with '
                                        f'those from the "{current_mode}" mode.',
                                options=["Yes", "No"])
        if confirm.get() == 'Cancel':
            return

        if self.appearance_mode == 'Light':
            for entry_id, button in enumerate(self.theme_palette_tiles):
                fg_colour = self.theme_palette_tiles[entry_id].cget('fg_color')
                self.theme_palette[str(entry_id)][1] = fg_colour
        else:
            for entry_id, button in enumerate(self.theme_palette_tiles):
                fg_colour = self.theme_palette_tiles[entry_id].cget('fg_color')
                self.theme_palette[str(entry_id)][0] = fg_colour

        self.save_theme_palette()
        self.json_state = 'dirty'
        self.set_option_states()

    def refresh_preview(self):
        """The _refresh_preview method, instructs the Preview Panel to perform a re-rendering of all widgets."""

        with open(self.wip_json, "w") as f:
            json.dump(self.theme_json_data, f, indent=2)
        self.send_command_json(command_type='program',
                               command='refresh',
                               parameters=[self.appearance_mode])

    def reload_preview(self):
        """The reload_preview method causes a full reload of the preview panel."""
        if self.process:
            self.send_command_json(command_type='program',
                                   command='quit',
                                   parameters=None)

        with open(self.wip_json, "w") as f:
            json.dump(self.theme_json_data, f, indent=2)
        self.process = None
        self.launch_preview()

        if self.tk_render_disabled.get():
            self.send_command_json(command_type='program',
                                   command='render_preview_disabled',
                                   parameters=None)
        else:
            self.send_command_json(command_type='program',
                                   command='render_preview_enabled',
                                   parameters=None)

        frame_mode = self.tk_swt_frame_mode.get()
        if frame_mode == 'base':
            self.send_command_json(command_type='program', command='render_base_frame')

    def close_panels(self):
        if self.json_state == 'dirty':
            confirm = CTkMessagebox(master=self.ctk_control_panel,
                                    title='Confirm Action',
                                    message=f'You have unsaved changes. Do you wish to save these before quitting?',
                                    options=["Yes", "No", "Cancel"])
            response = confirm.get()
            if response == 'Cancel':
                return
            elif response == 'Yes':
                self.save_theme()

        if self.process:
            self.send_command_json(command_type='program',
                                   command='quit',
                                   parameters=None)

        self.save_controller_geometry()
        self.ctk_control_panel.destroy()

    def launch_preview(self):
        appearance_mode_ = self.appearance_mode
        with open(self.wip_json, "w") as f:
            json.dump(self.theme_json_data, f, indent=2)

        designer = os.path.basename(__file__)
        if platform.system() == 'Windows':
            designer = designer.replace('.py', '.bat')
        else:
            designer = designer.replace('.py', '.sh')

        if self.process is None:
            designer = APP_HOME / designer
            program = [designer, '-a', appearance_mode_, '-t', self.wip_json]
            print(f'Launching designer: {designer}')
            self.process = sp.Popen(program)
            listener_started = False
            # Wait for Preview Pamel to start the listener.
            # We expect a semaphore file to be created when this
            # is so.
            sleep_count = 0
            while not listener_started:
                sleep_count += 1
                if LISTENER_FILE.exists():
                    listener_started = True
                if sleep_count > 80:
                    confirm = CTkMessagebox(master=self.ctk_control_panel,
                                            title='Please Upgrade CustomTkinter',
                                            message=f'TIMEOUT: Waited too long for preview listener!\n\n'
                                                    f'Ensure that only one instance of {__title__} is running is '
                                                    f'running and that no other process is using the port..',
                                            option_1='OK')
                    print('ERROR: Waited too long for listener!')
                    print(f'       Ensure that only one instance of {__title__} is running.')
                    if confirm.get() == 'OK':
                        exit(1)
                time.sleep(0.1)

    def restore_controller_geometry(self):
        default_geometry = f"{ControlPanel.PANEL_WIDTH}x{ControlPanel.PANEL_HEIGHT}+347+93"
        controller_geometry = mod.preference_setting(db_file_path=DB_FILE_PATH,
                                                     scope='window_geometry',
                                                     preference_name='control_panel', default=default_geometry)
        self.ctk_control_panel.geometry(controller_geometry)
        self.ctk_control_panel.resizable(False, True)

    def save_controller_geometry(self):
        """Save the control panel geometry to the repo, for the next time the program is launched."""
        geometry_row = mod.preference_row(db_file_path=DB_FILE_PATH,
                                          scope='window_geometry',
                                          preference_name='control_panel')
        panel_geometry = self.ctk_control_panel.geometry()
        geometry_row["preference_value"] = panel_geometry
        mod.upsert_preference(db_file_path=DB_FILE_PATH, preference_row_dict=geometry_row)

    def save_theme(self):
        if 'provenance' in self.theme_json_data:
            # current dateTime
            now = datetime.now()
            # convert to string
            date_modified = now.strftime("%b %d %Y %H:%M:%S")
            theme_name = self.source_json_file
            theme_name = os.path.splitext(theme_name)[0]
            theme_name = os.path.basename(theme_name)
            self.theme_json_data['provenance']['theme name'] = theme_name
            self.theme_json_data['provenance']['last modified'] = date_modified
            if self.theme_author:
                self.theme_json_data['provenance']['last modified by'] = self.theme_author
            else:
                self.theme_json_data['provenance']['last modified by'] = 'Unknown'

        with open(self.wip_json, "w") as f:
            json.dump(self.theme_json_data, f, indent=2)
        shutil.copyfile(self.wip_json, self.source_json_file)
        theme_file_name = os.path.basename(self.source_json_file)
        self.json_state = 'clean'
        self.btn_reset.configure(state=tk.DISABLED)
        self.btn_save.configure(state=tk.DISABLED)
        self.status_bar.set_status_text(status_text=f'Theme file, {theme_file_name}, saved successfully!')
        self.save_theme_palette()

    def get_tooltips_setting(self):
        self.enable_tooltips = int(self.tk_enable_tooltips.get())

    def get_palette_label_setting(self):
        self.enable_palette_labels = int(self.tk_enable_palette_labels.get())

    def get_last_theme_on_start(self):
        self.last_theme_on_start = int(self.tk_last_theme_on_start.get())

    def get_single_click_paste_setting(self):
        self.enable_single_click_paste = int(self.tk_enable_single_click_paste.get())


class AppearanceMode(Enum):
    LIGHT: int = 0
    DARK: int = 1

    @staticmethod
    def mode_int(self, mode: str):
        if mode.lower() == 'light':
            return 0
        elif mode.lower() == 'dark':
            return 1

    @staticmethod
    def mode(self, mode_int: str):
        if mode_int == AppearanceMode.LIGHT:
            return 'Light'
        elif mode_int == AppearanceMode.DARK:
            return 'Dark'


class WidgetType(Enum):
    CTK = 1
    TOP_LEVEL = 2
    FRAME = 3
    SCROLLBAR = 4
    BUTTON = 5
    LABEL = 6
    ENTRY = 7
    OPTIONMENU = 8
    COMBO_BOX = 9
    SWITCH = 10
    SLIDER = 11
    PROGRESSBAR = 12
    CHECKBOX = 13
    RADIOBUTTON = 14


"""
@dataclass
class Widget(ABC):
    def __init__(self, widget_type: WidgetType, colours: list):
        self.widget = {"widget_type": widget_type,
                        "widget_properties": {"colours": colours}}
        self.widget_type = widget_type
        self.colours = colours
        self.light_mode_colour: str = colours[0]
        self.dark_mode_colour: str = colours[1]

    @property
    @abstractmethod
    def widget(self):
        pass

    @widget.setter
    def widget(self, colours: list):
        pass


@dataclass
class Button(Widget):
    @property
    def widget(self, widget_type: WidgetType, colours: list):
        pass

    widget_type = WidgetType.BUTTON


@dataclass
class WidgetShape(ABC):
    property: str
    corner_radius: int


@dataclass
class CommandController:
    def __init__(self, control_panel: Type[ControlPanel]):
        self.control = control_panel
        self.widgets = list[Widget] = field(default_factory=list)

    def execute_command(self, command_type: str, command):
        pass
"""

if __name__ == "__main__":
    ap = argparse.ArgumentParser(formatter_class=SortingHelpFormatter
                                 , description=f"{PROG}: Welcome to CTk Theme Designer, which is designed to help you "
                                               f"design, themes to run with the CustomTkinter framework")

    ap.add_argument("-a", '--set-appearance', required=False, action="store",
                    help="Set the CustomTkinter appearance mode. Used for colour preview only.",
                    dest='appearance_mode', default='Dark')

    ap.add_argument("-t", '--set-theme', required=False, action="store",
                    help="Set the CustomTkinter theme. Used for colour preview only.",
                    dest='theme_file', default=None)

    args_list = vars(ap.parse_args())
    appearance_mode = args_list["appearance_mode"]
    theme_file = args_list["theme_file"]

    # If theme is set, we assume we are running in "preview" mode.
    if theme_file is not None:
        running_preview = True
        run_preview_panel(appearance_mode=appearance_mode, theme_file=theme_file)
    else:
        controller = ControlPanel()
