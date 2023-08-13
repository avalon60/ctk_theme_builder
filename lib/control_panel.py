"""Class container for the Control Panel class"""

import customtkinter as ctk
import tkinter as tk
import lib.cbtk_kit as cbtk
import lib.ctk_theme_builder_m as mod

from lib.harmonics_dialog import HarmonicsDialog
from lib.preferences import PreferencesDialog
from lib.theme_merger import ThemeMerger

from lib.about import About
from lib.provenance_dialog import ProvenanceDialog
from lib.geometry_dialog import GeometryDialog
import operator
import platform
import pyperclip
from pathlib import Path
import time
from datetime import datetime
import shutil
import os
import subprocess as sp
from tkinter.colorchooser import askcolor
import json
from lib.CTkToolTip import *
from CTkMessagebox import CTkMessagebox


CTK_SITE_PACKAGES = mod.CTK_SITE_PACKAGES
CTK_ASSETS = mod.CTK_ASSETS
CTK_THEMES = mod.CTK_THEMES
APP_IMAGES = mod.APP_IMAGES

HEADING1 = mod.HEADING1
HEADING2 = mod.HEADING2
HEADING3 = mod.HEADING3
HEADING4 = mod.HEADING4

REGULAR_TEXT = cbtk.REGULAR_TEXT
SMALL_TEXT = mod.SMALL_TEXT
LISTENER_FILE = mod.LISTENER_FILE
PROG_NAME = mod.PROG_NAME

APP_HOME = mod.APP_HOME
APP_THEMES_DIR = mod.APP_THEMES_DIR
DB_FILE_PATH = mod.DB_FILE_PATH
ETC_DIR = mod.ETC_DIR
TEMP_DIR = mod.TEMP_DIR
# Grab the JSON for the default view.
DEFAULT_VIEW = mod.DEFAULT_VIEW
VIEWS_DIR = mod.VIEWS_DIR
default_view_file = VIEWS_DIR / f'{DEFAULT_VIEW}.json'
DEFAULT_VIEW_WIDGET_ATTRIBUTES = mod.json_dict(json_file_path=default_view_file)
class ControlPanel(ctk.CTk):
    _theme_json_dir: Path
    THEME_PALETTE_TILES = 16
    THEME_PALETTE_TILE_WIDTH = 8
    THEME_PALETTE_ROWS = 2

    command_stack = mod.CommandStack()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.theme_palette_tiles = []
        self.palette_button_list = []
        self.protocol("WM_DELETE_WINDOW", self.block_window_close)
        self.control_panel_scaling = None
        self.preview_panel_scaling = None
        self.qa_application_scaling = None
        self.listener_port = None
        self.theme_json_data = {}
        self.top_frame = "top"
        # Grab the JSON for one of the JSON files released with the
        # installed instance of CustomTkinter. We use this later
        # to back-fill any missing properties when we open a theme.
        green_theme_file = CTK_THEMES / 'green.json'
        with open(green_theme_file) as json_file:
            self.reference_theme_json = json.load(json_file)

        self.theme = None
        self.ASSETS_DIR = mod.ASSETS_DIR
        self.log_dir = mod.LOG_DIR
        self.CONFIG_DIR = mod.CONFIG_DIR
        self.ETC_DIR = mod.ETC_DIR
        self.VIEWS_DIR = mod.VIEWS_DIR
        self.palettes_dir = mod.PALETTES_DIR
        self.listener_port = mod.listener_port()
        self.qa_launched = False

        icon_photo = tk.PhotoImage(file=APP_IMAGES / 'bear-logo-colour-dark.png')
        self.iconphoto(False, icon_photo)
        self.new_theme_json_dir = None
        self.wip_json = None

        if LISTENER_FILE.exists():
            try:
                os.remove(LISTENER_FILE)
            except PermissionError:
                print(f'ERROR: Could not remove listener semaphore file, {LISTENER_FILE}.')
                print(f'Only one instance of {PROG_NAME}, should be running.')
                exit(0)

        # Initialise class properties
        self.process = None

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

        self.confirm_cascade = mod.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                      preference_name='confirm_cascade')

        self.enable_palette_labels = mod.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                            preference_name='enable_palette_labels')

        self.enable_single_click_paste = mod.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                                preference_name='enable_single_click_paste')

        self.last_theme_on_start = mod.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                          preference_name='last_theme_on_start')

        if self.last_theme_on_start == 'NO_DATA_FOUND':
            self.last_theme_on_start = mod.new_preference_dict(scope='user_preference',
                                                               preference_name='last_theme_on_start',
                                                               data_type='int', preference_value=0)
            mod.upsert_preference(db_file_path=DB_FILE_PATH, preference_row_dict=self.last_theme_on_start)

        self.control_panel_scaling_pct = mod.preference_setting(db_file_path=DB_FILE_PATH,
                                                                scope='scaling',
                                                                preference_name='control_panel')
        control_panel_scale = mod.scaling_float(scale_pct=self.control_panel_scaling_pct)
        ctk.set_widget_scaling(control_panel_scale)

        self.preview_panel_scaling_pct = mod.preference_setting(db_file_path=DB_FILE_PATH,
                                                                scope='scaling',
                                                                preference_name='preview_panel')

        self.qa_application_scaling_pct = mod.preference_setting(db_file_path=DB_FILE_PATH,
                                                                 scope='scaling',
                                                                 preference_name='qa_application')

        self.theme_json_dir = mod.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                     preference_name='theme_json_dir')

        # If no row found for the user theme directory, fall back to the
        # default location.
        if self.theme_json_dir == 'NO_DATA_FOUND':
            self.theme_json_dir = APP_HOME / 'user_themes'
            theme_dir_row = mod.new_preference_dict(scope='user_preference',
                                                    preference_name='theme_json_dir',
                                                    preference_value=str(self.theme_json_dir),
                                                    data_type='Path')
            mod.upsert_preference(db_file_path=DB_FILE_PATH, preference_row_dict=theme_dir_row)

        elif not self.theme_json_dir.exists():
            self.theme_json_dir = APP_HOME / 'user_themes'
            theme_dir_row = mod.new_preference_dict(data_type='Path',
                                                    scope='user_preference',
                                                    preference_name='theme_json_dir',
                                                    preference_value=self.theme_json_dir)
            theme_dir_row['preference_value'] = str(theme_dir_row['preference_value'])
            mod.upsert_preference(db_file_path=DB_FILE_PATH, preference_row_dict=theme_dir_row)

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

        self.rowconfigure(3, weight=1)
        self.columnconfigure(0, weight=1)

        self.title('CTk Theme Builder')

        # Instantiate Frames
        title_frame = ctk.CTkFrame(master=self)
        title_frame.pack(fill="both", expand=0)

        self.frm_control = ctk.CTkFrame(master=self)
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
        self.status_bar = cbtk.CBtkStatusBar(master=self,
                                             status_text_life=30,
                                             use_grid=False)
        self.bind("<Configure>", self.status_bar.auto_size_status_bar)

        # Populate Frames
        self.lbl_title = ctk.CTkLabel(master=title_frame, text='Control Panel', font=HEADING4, anchor='w')
        self.lbl_title.grid(row=0, column=0, columnspan=2, sticky='w', padx=10, pady=5)
        master = title_frame.columnconfigure(0, weight=1)

        self.lbl_theme = ctk.CTkLabel(master=self.frm_button, text='Select Theme:')
        self.lbl_theme.grid(row=1, column=0, sticky='w', pady=(10, 0), padx=(15, 10))

        self.json_files = mod.user_themes_list()
        initial_display = mod.user_themes_list()
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

        self.tk_swt_frame_mode = ctk.StringVar(value=self.top_frame)
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
                                            border_width=1,
                                            padding=(10, 10),
                                            corner_radius=6,
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

        if self.enable_tooltips:
            frame_mode_tooltip = CTkToolTip(self.swt_render_disabled,
                                            wraplength=400,
                                            justify="left",
                                            border_width=1,
                                            padding=(10, 10),
                                            corner_radius=6,
                                            message='Enable this switch, to preview widget appearances in disabled '
                                                    'mode.')

        self.lbl_widget_view = ctk.CTkLabel(master=self.frm_button,
                                            text='Properties View:')
        self.lbl_widget_view.grid(row=9, column=0, sticky='w', pady=(20, 0), padx=(15, 10))

        self.widget_categories = mod.all_widget_categories(DEFAULT_VIEW_WIDGET_ATTRIBUTES)
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
                                             border_width=1,
                                             padding=(10, 10),
                                             corner_radius=6,
                                             message='Views help you to target specific widgets, or groups of  '
                                                     'related widgets, and their associated properties. ')

        self.lbl_filter = ctk.CTkLabel(master=self.frm_button, text='Filter View:')
        self.lbl_filter.grid(row=11, column=0, sticky='w', pady=(10, 0), padx=(15, 10))

        self.widget_categories = mod.all_widget_categories(DEFAULT_VIEW_WIDGET_ATTRIBUTES)
        self.opm_properties_filter = ctk.CTkOptionMenu(master=self.frm_button,
                                                       values=self.widget_categories,
                                                       command=self.set_filtered_widget_display,
                                                       state=tk.DISABLED)
        self.opm_properties_filter.grid(row=12, column=0)
        if self.enable_tooltips:
            filter_view_tooltip = CTkToolTip(self.opm_properties_filter,
                                             wraplength=400,
                                             justify="left",
                                             border_width=1,
                                             padding=(10, 10),
                                             corner_radius=6,
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
                                      border_width=1,
                                      padding=(10, 10),
                                      corner_radius=6,
                                      message='The "Refresh Preview" button causes a reload of the preview panel, and '
                                              're-paints the preview, with the currently selected theme / appearance '
                                              'mode.')

        self.btn_undo = ctk.CTkButton(master=button_frame,
                                      text='Undo',
                                      state=tk.DISABLED,
                                      command=self.undo_change)
        self.btn_undo.grid(row=15, column=0, padx=5, pady=(30, 5))

        self.btn_redo = ctk.CTkButton(master=button_frame,
                                      text='Redo',
                                      state=tk.DISABLED,
                                      command=self.redo_change)
        self.btn_redo.grid(row=17, column=0, padx=5, pady=(5, 5))

        self.btn_reset = ctk.CTkButton(master=button_frame,
                                       text='Reset',
                                       state=tk.DISABLED,
                                       command=self.reset_theme)
        self.btn_reset.grid(row=18, column=0, padx=5, pady=(5, 5))

        self.btn_create = ctk.CTkButton(master=button_frame,
                                        text='New Theme',
                                        command=self.create_theme)
        self.btn_create.grid(row=19, column=0, padx=5, pady=(30, 5))

        self.btn_sync_modes = ctk.CTkButton(master=button_frame,
                                            text='Sync Modes',
                                            state=tk.DISABLED,
                                            command=self.sync_appearance_mode)
        self.btn_sync_modes.grid(row=20, column=0, padx=5, pady=(5, 5))
        if self.enable_tooltips:
            sync_tooltip = CTkToolTip(self.btn_sync_modes,
                                      wraplength=250,
                                      justify="left",
                                      border_width=1,
                                      padding=(10, 10),
                                      corner_radius=6,
                                      message='Copies the color settings of the selected widget properties, for the '
                                              'currently selected Appearance Mode ("Dark"/"Light"), to its counterpart '
                                              'mode.')

        self.btn_sync_palette = ctk.CTkButton(master=button_frame,
                                              text='Sync Palette',
                                              state=tk.DISABLED,
                                              command=self.sync_theme_palette)
        self.btn_sync_palette.grid(row=21, column=0, padx=5, pady=(5, 5))
        if self.enable_tooltips:
            sync_tooltip = CTkToolTip(self.btn_sync_modes,
                                      wraplength=250,
                                      justify="left",
                                      border_width=1,
                                      padding=(10, 10),
                                      corner_radius=6,
                                      message='Copies the Theme Palette color settings of the selected appearance '
                                              'mode ("Light"/"Dark") to its counterpart mode')

        self.btn_save = ctk.CTkButton(master=button_frame,
                                      text='Save',
                                      state=tk.DISABLED,
                                      command=self.save_theme)
        self.btn_save.grid(row=22, column=0, padx=5, pady=(30, 5))

        self.btn_save_as = ctk.CTkButton(master=button_frame,
                                         text='Save As',
                                         state=tk.DISABLED,
                                         command=self.save_theme_as)
        self.btn_save_as.grid(row=25, column=0, padx=5, pady=(5, 5))

        self.btn_delete = ctk.CTkButton(master=button_frame,
                                        text='Delete',
                                        state=tk.DISABLED,
                                        command=self.delete_theme)
        self.btn_delete.grid(row=27, column=0, padx=5, pady=(5, 5))

        btn_quit = ctk.CTkButton(master=button_frame, text='Quit', command=self.close_panels)
        btn_quit.grid(row=30, column=0, padx=5, pady=(60, 5))

        self.create_menu()

        if int(base_min_version) > int(base_ctk_version):
            print(f'WARNING: The version of CustomTkinter, on your system, is incompatible. Please upgrade to '
                  f'CustomTkinter {self.min_ctk_version} or later.')
            confirm = CTkMessagebox(master=self,
                                    title='Please Upgrade CustomTkinter',
                                    message=f'The version of CustomTkinter, on your system, is incompatible. '
                                            f'Please upgrade to CustomTkinter {self.min_ctk_version} or later.',
                                    option_1='OK')
            if confirm.get() == 'OK':
                exit(1)

        self.load_theme()

        self.mainloop()

    def block_window_close(self):
        pass

    def flip_appearance_modes(self):
        if self.json_state == 'dirty':
            confirm = CTkMessagebox(master=self,
                                    title='Acknowledge',
                                    message=f'You have unsaved changes. You must Save or Reset any changes, '
                                            f'before using the Flip Modes option.',
                                    options=["OK"])
            response = confirm.get()
            if response == 'OK':
                return
        selected_theme = self.opm_theme.get()
        confirm = CTkMessagebox(master=self,
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
        if not cbtk.valid_colour(new_colour):
            self.status_bar.set_status_text(status_text=f'Paste action ignored - not a valid colour code.')
            return
        prev_colour = self.widgets[widget_property]["colour"]
        # We don't know whether the widget is displayed for sure, when we are using cascade from the colour palette
        # region, so we need to check, the selected view, may not include the widget.
        if self.widgets[widget_property]['tile'].winfo_exists():
            self.widgets[widget_property]['tile'].configure(fg_color=new_colour)
            self.widgets[widget_property]['colour'] = new_colour
        appearance_mode_index = cbtk.str_mode_to_int(self.appearance_mode)
        # At this point widget_property is a concatenation of the widget type and widget property.
        # We need to split these out. The widget_property_split function, transforms these for us.
        widget_type, split_property = mod.widget_property_split(widget_property=widget_property)
        self.theme_json_data[widget_type][split_property][appearance_mode_index] = new_colour

        if prev_colour != new_colour and widget_property in mod.FORCE_COLOR_REFRESH_PROPERTIES:
            # Then either this isn't a real widget, or is a property which cannot be updated
            # dynamically, and so we force a refresh to update the widgets dependent upon its properties.
            self.refresh_preview()
        elif prev_colour != new_colour:
            # Grab a change vector - we need it for undo/redo
            change_vector = mod.PropertyVector(command_type='colour',
                                               command='update_widget_colour',
                                               component_type=widget_type,
                                               component_property=split_property,
                                               new_value=new_colour,
                                               old_value=prev_colour)

            self.command_stack.exec_command(property_vector=change_vector)
            self.json_state = 'dirty'
            self.set_option_states()

    def create_theme_palette(self, theme_name):
        self.theme_palette = mod.json_dict(json_file_path=ETC_DIR / 'default_palette.json')
        palette_json = theme_name.replace('.json', '') + '.json'
        self.palette_file = self.palettes_dir / palette_json
        with open(self.palette_file, "w") as f:
            json.dump(self.theme_palette, f, indent=2)

    def create_menu(self):
        # Set up the core of our menu
        self.des_menu = cbtk.CBtkMenu(self, tearoff=0)
        foreground = cbtk.get_color_from_name(widget_type='CTkLabel', widget_property='text_color')
        background = cbtk.get_color_from_name(widget_type='CTkToplevel', widget_property='fg_color')
        self.config(menu=self.des_menu)

        # Now add a File sub-menu option
        self.file_menu = cbtk.CBtkMenu(self.des_menu, tearoff=0)
        self.des_menu.add_cascade(label='File', menu=self.file_menu)
        self.file_menu.add_command(label='Refresh Preview', command=self.reload_preview)
        self.file_menu.add_separator()
        self.file_menu.add_command(label='Undo', command=self.undo_change)
        self.file_menu.add_command(label='Redo', command=self.redo_change)
        self.file_menu.add_command(label='Reset', command=self.reset_theme)
        self.file_menu.add_separator()
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
        self.file_menu.add_command(label='Launch QA App', command=self.launch_qa_app, state=tk.DISABLED)
        self.file_menu.add_separator()
        self.file_menu.add_command(label='Quit', command=self.close_panels)

        # Now add a Tools sub-menu option
        self.tools_menu = cbtk.CBtkMenu(self.des_menu, tearoff=0)
        self.des_menu.add_cascade(label='Tools', menu=self.tools_menu)
        self.tools_menu.add_command(label='Preferences', command=self.launch_preferences_dialog)
        self.tools_menu.add_command(label='Colour Harmonics', command=self.launch_harmony_dialog, state=tk.DISABLED)
        self.tools_menu.add_command(label='Merge Themes', command=self.launch_theme_merger)

        self.tools_menu.add_command(label='About', command=self.about)

        self.set_option_states()

    def launch_theme_merger(self):
        theme_merger = ThemeMerger(master=self)
        self.wait_window(theme_merger)
        self.json_files = mod.user_themes_list()
        self.opm_theme.configure(values=self.json_files)
        if theme_merger.open_on_merge():
            new_theme_name = theme_merger.new_theme_name()
            self.opm_theme.set(new_theme_name)
            self.load_theme()

    def copy_property_colour(self, event=None, widget_property=None):
        colour = None
        try:
            colour = self.widgets[widget_property]['tile'].cget('fg_color')
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
        about_dialog = About()

    def launch_preferences_dialog(self):
        preferences_dialog = PreferencesDialog(master=self)
        self.wait_window(preferences_dialog)
        action = preferences_dialog.action
        listener_port = mod.listener_port()
        self.update()
        self.block_window_close()
        if listener_port != self.listener_port:
            self.reload_preview()
        self.load_preferences()
        self.status_bar.set_status_text(status_text=f'Preference updates {action}.')

    def launch_provenance_dialog(self):
        provenance_dialog = ProvenanceDialog()
        theme_name = self.theme_json_data["provenance"]["theme name"]
        created_with = self.theme_json_data["provenance"]["created with"]
        date_created = self.theme_json_data["provenance"]["date created"]
        authors_name = self.theme_json_data["provenance"]["theme author"]
        last_modified_by = self.theme_json_data["provenance"]["last modified by"]
        last_modified_date = self.theme_json_data["provenance"]["last modified"]
        harmony_method = self.theme_json_data["provenance"]["harmony method"]
        keystone_colour = self.theme_json_data["provenance"]["keystone colour"]
        provenance_dialog.modify_property(property_name='theme_name', value=theme_name)
        provenance_dialog.modify_property(property_name='authors_name', value=authors_name)
        provenance_dialog.modify_property(property_name='date_created', value=date_created)
        provenance_dialog.modify_property(property_name='created_with', value=created_with)
        provenance_dialog.modify_property(property_name='last_modified_by', value=last_modified_by)
        provenance_dialog.modify_property(property_name='last_modified_date', value=last_modified_date)
        provenance_dialog.modify_property(property_name='harmony_method', value=harmony_method)
        provenance_dialog.modify_property(property_name='keystone_colour', value=keystone_colour)

    def launch_qa_app(self):
        if self.wip_json is None:
            return
        self.update_wip_file()
        if platform.system() == 'Windows':
            qa_app_launcher = 'ctk_theme_builder_qa_app.bat'
        else:
            qa_app_launcher = 'ctk_theme_builder_qa_app.sh'

        qa_app = APP_HOME / qa_app_launcher
        program = [qa_app, '-a', self.appearance_mode, '-t', self.wip_json]
        self.process = sp.Popen(program)
        self.qa_launched = True

    def load_preferences(self):

        control_panel_theme = mod.preference_setting(db_file_path=DB_FILE_PATH,
                                                     scope='user_preference', preference_name='control_panel_theme')

        control_panel_theme = control_panel_theme + '.json'

        self.control_panel_theme = str(APP_THEMES_DIR / control_panel_theme)

        self.control_panel_mode = mod.preference_setting(db_file_path=DB_FILE_PATH,
                                                         scope='user_preference', preference_name='control_panel_mode')

        self.last_theme_on_start = mod.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                          preference_name='last_theme_on_start')

        self.theme_author = mod.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                   preference_name='theme_author')

        self.enable_tooltips = mod.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                      preference_name='enable_tooltips')

        self.confirm_cascade = mod.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                      preference_name='confirm_cascade')

        self.enable_palette_labels = mod.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                            preference_name='enable_palette_labels')

        self.enable_single_click_paste = mod.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                                preference_name='enable_single_click_paste')

        self.shade_adjust_differential = mod.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                                preference_name='shade_adjust_differential')

        self.harmony_contrast_differential = mod.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                                    preference_name='harmony_contrast_differential')

        self.theme_json_dir = mod.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                     preference_name='theme_json_dir')

        self.control_panel_scaling = mod.preference_setting(db_file_path=DB_FILE_PATH,
                                                            scope='scaling',
                                                            preference_name='control_panel')

        self.preview_panel_scaling = mod.preference_setting(db_file_path=DB_FILE_PATH,
                                                            scope='scaling',
                                                            preference_name='preview_panel')

        self.qa_application_scaling = mod.preference_setting(db_file_path=DB_FILE_PATH,
                                                             scope='scaling',
                                                             preference_name='qa_application')

        self.listener_port = mod.preference_setting(db_file_path=DB_FILE_PATH,
                                                    scope='user_preference',
                                                    preference_name='listener_port')

        self.min_ctk_version = mod.preference_setting(db_file_path=DB_FILE_PATH, scope='system',
                                                      preference_name='min_ctk_version')

    def sync_palette_mode_colours(self):
        """Sync the theme colour palette colours to both modes."""
        for entry_id, button in enumerate(self.theme_palette_tiles):
            fg_colour = self.theme_palette_tiles[entry_id].cget('fg_color')
            self.theme_palette[str(entry_id)][0] = fg_colour
        for entry_id, button in enumerate(self.theme_palette_tiles):
            fg_colour = self.theme_palette_tiles[entry_id].cget('fg_color')
            self.theme_palette[str(entry_id)][1] = fg_colour
    def stash_theme_palette(self, mode):
        """Stash the theme colour palette colours to disk. We do this when switching appearance mode."""
        for entry_id, button in enumerate(self.theme_palette_tiles):
            fg_colour = self.theme_palette_tiles[entry_id].cget('fg_color')
            self.theme_palette[str(entry_id)][mode] = fg_colour

        with open(self.wip_palette_file, "w") as f:
            json.dump(self.theme_palette, f, indent=2)

    def load_stashed_theme_palette(self, mode):
        self.theme_palette = mod.json_dict(json_file_path=self.wip_palette_file)
        # Marry the palette buttons to their palette colours
        try:
            for entry_id, button in enumerate(self.theme_palette_tiles):
                colour = self.theme_palette[str(entry_id)][mode]
                hover_colour = cbtk.contrast_colour(colour)
                button.configure(fg_color=colour, hover_color=hover_colour)
        except IndexError:
            pass

    def save_theme_palette(self, theme_name: str = None):
        """Save the colour palette colours back to disk."""
        if theme_name is None:
            palette_json_file = self.source_palette_file
        else:
            palette_json_file = theme_name.replace('.json', '') + '.json'

        self.source_palette_file = self.palettes_dir / palette_json_file

        self.theme_palette = mod.json_dict(json_file_path=self.wip_palette_file)

        # Update the button colour settings to the self.theme_palette dictionary
        self.palette_file = self.palettes_dir / palette_json_file
        if self.appearance_mode.lower() == 'light':
            mode = 0
        else:
            mode = 1
        for entry_id, button in enumerate(self.theme_palette_tiles):
            fg_colour = self.theme_palette_tiles[entry_id].cget('fg_color')
            self.theme_palette[str(entry_id)][mode] = fg_colour

        with open(self.wip_palette_file, "w") as f:
            json.dump(self.theme_palette, f, indent=2)

        shutil.copyfile(self.wip_palette_file, self.source_palette_file)

    def render_geometry_buttons(self):
        """Set up the geometry buttons near the top of the Control Panel"""

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
                                         text='CheckBox',
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
        geometry_dialog = GeometryDialog(master=self, widget_type=widget_type,
                                         command_stack=self.command_stack,
                                         theme_json_data=self.theme_json_data,
                                         appearance_mode=self.appearance_mode)
        if geometry_dialog.force_refresh:
            # This is a property which cannot be updated
            # dynamically, and so we force a refresh to update
            # the widget.
            self.refresh_preview(set_scaling=False)

    def set_option_states(self):
        """This function sets the button and menu option states. The states are set based upon a combination of,
        whether a theme is currently selected, and the state of the theme ('dirty'/'clean')"""
        if self.command_stack.undo_length() > 0:
            # Reminder: do not be tempted to set the state to 'clean' where undo_length == 0
            # We have operations other than undo/redo which dirty the JSON. Setting to 'clean'
            # will break the Reset option for such operations.
            self.json_state = 'dirty'

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
        self.file_menu.entryconfig('Launch QA App', state=tk_state)

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

        if self.command_stack.undo_length() > 0:
            self.btn_undo.configure(state=ctk.NORMAL)
            self.file_menu.entryconfig('Undo', state=ctk.NORMAL)
        else:
            self.btn_undo.configure(state=ctk.DISABLED)
            self.file_menu.entryconfig('Undo', state=ctk.DISABLED)

        if self.command_stack.redo_length() > 0:
            self.btn_redo.configure(state=ctk.NORMAL)
            self.file_menu.entryconfig('Redo', state=ctk.NORMAL)
        else:
            self.btn_redo.configure(state=ctk.DISABLED)
            self.file_menu.entryconfig('Redo', state=ctk.DISABLED)

        if self.harmony_palette_running:
            self.tools_menu.entryconfig('Colour Harmonics', state=tk.DISABLED)
        elif not self.harmony_palette_running and self.theme:
            self.tools_menu.entryconfig('Colour Harmonics', state=tk.NORMAL)

    def switch_preview_appearance_mode(self, event='event'):
        """Actions to choice of preview panel's appearance mode (Light / Dark)"""
        preview_appearance_mode = self.tk_seg_mode.get()
        if preview_appearance_mode == 'Light Mode':
            self.appearance_mode = 'Light'
            old_value = 'Dark'
            old_mode_index = 1
            new_mode_index = 0
        else:
            self.appearance_mode = 'Dark'
            old_value = 'Light'
            old_mode_index = 0
            new_mode_index = 1

        if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='auto_save',
                                           preference_name='appearance_mode',
                                           preference_value=self.appearance_mode):
            print(f'Row miss: on update of auto save of selected theme.')

        self.lbl_palette_header.configure(text=f'Theme Palette ({preview_appearance_mode})')
        self.update_wip_file()
        self.stash_theme_palette(mode=old_mode_index)
        self.render_widget_properties()
        self.load_stashed_theme_palette(mode=new_mode_index)
        # We only log change vectors for appearance mode, where there might be colour changes involved.
        if self.command_stack.undo_length() > 0 or self.command_stack.redo_length() > 0:
            change_vector = mod.PropertyVector(command_type='program',
                                               command='set_appearance_mode',
                                               new_value=self.appearance_mode,
                                               old_value=old_value)

            self.command_stack.exec_command(property_vector=change_vector)
        else:
            mod.send_command_json(command_type='program',
                                  command='set_appearance_mode',
                                  parameters=[self.appearance_mode])

        # Ensure we honor the Top Frame switch setting
        self.set_option_states()
        self.toggle_frame_mode()

    def render_theme_palette(self):
        render_labels = self.enable_palette_labels
        palette_entries = mod.colour_palette_entries(db_file_path=DB_FILE_PATH)
        menus = []
        self.theme_palette_tiles.clear()

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

        self.palette_button_list.clear()
        for palette_id, tile_dict in enumerate(palette_entries):
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
            self.palette_button_list.append(btn_colour_tile)
            if render_labels:
                pad_y = 0
            else:
                pad_y = 5
            btn_colour_tile.grid(row=row, column=col, padx=padx, pady=1)
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

            if self.cascade_enabled(palette_id=palette_id):
                context_menu.add_separator()
                context_menu.add_command(label="Cascade colour",
                                         command=lambda button_id=entry_id: self.cascade_colour(button_id))

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

    def cascade_colour(self, palette_id):
        cascade_dict_list = mod.cascade_dict(palette_id=palette_id)
        property_colour = self.palette_button_list[palette_id].cget("fg_color")
        cascade_impact = mod.cascade_display_string(palette_id=palette_id)

        if self.confirm_cascade:
            confirm = CTkMessagebox(master=self,
                                    title='Confirm Action',
                                    message=f'The following properties will be updated to the selected colour:\n'
                                            f'{cascade_impact}\n\n'
                                            f'Do you wish to continue?',
                                    options=["Yes", "No"])
            response = confirm.get()
            if response == 'No':
                return

        for _property in cascade_dict_list:
            _widget_property = f'{_property["widget_type"]}: {_property["widget_property"]}'
            if _property["widget_type"] != 'CTk':
                # Except for the CTk() class, we strip out the CTk string,
                # from the widget name, for display purposes.
                _widget_property = _widget_property.replace('CTk', '')

            # We call the paste_colour method here, overriding the cut/paste mode, by supplying the
            # property colour directly, as a parameter.
            self.paste_colour(event=None, widget_property=_widget_property, property_colour=property_colour)

    def cascade_enabled(self, palette_id: int) -> bool:
        return mod.cascade_enabled(palette_id=palette_id)

    def toggle_frame_mode(self):
        """We need the ability to render the frames in the preview panel as they would appear when we have a top frame
        (a frame whose parent widget is a frame. Conversely, we also need to see how our other widgets render within
        a single frame. This method toggles the preview panel, between the 2 states."""
        if not self.theme:
            return
        frame_mode = self.tk_swt_frame_mode.get()
        if frame_mode == 'top':
            mod.send_command_json(command_type='program', command='render_top_frame')
        else:
            mod.send_command_json(command_type='program', command='render_base_frame')
        self.top_frame = frame_mode

    def toggle_render_disabled(self):
        render_state = self.swt_render_disabled.get()
        if render_state:
            mod.send_command_json(command_type='program', command='render_preview_disabled')
        else:
            mod.send_command_json(command_type='program', command='render_preview_enabled')

    def update_properties_filter(self, view_name):
        """When a different view is selected, we need to update the Properties Filter list accordingly. This method,
        loads the requisite JSON files and derives the new list for us. """
        view_file = str(VIEWS_DIR / view_name) + '.json'
        view_file = Path(view_file)
        self.widget_attributes = mod.json_dict(json_file_path=view_file)
        self.widget_categories = mod.all_widget_categories(self.widget_attributes)
        self.opm_properties_filter.configure(values=self.widget_categories)
        # Cause the Filters to be set to 'All', for the
        # selected view and update the display accordingly.
        self.opm_properties_filter.set('All')
        self.set_filtered_widget_display()
        # self.send_preview_command('Update properties filter...')

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

    def undo_change(self):
        undo_text, _command_type, _widget_type, _widget_property, _property_value = self.command_stack.undo_command()
        _command = _widget_type
        if _command_type == 'colour':
            self.update_rendered_widget(widget_type=_widget_type,
                                        widget_property=_widget_property, property_value=_property_value)

        elif _command == 'set_appearance_mode':
            # _property_value is 'Light' or 'Dark'
            self.tk_seg_mode.set(_property_value + ' Mode')

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
            self.update_wip_file()
            self.load_theme_palette()
            self.render_widget_properties()

        elif _command_type == 'palette_colour':
            palette_button_id = _widget_property
            self.set_palette_colour(palette_button_id=palette_button_id, colour=_property_value)

        self.set_option_states()
        self.status_bar.set_status_text(
            status_text=undo_text)

    def redo_change(self):
        redo_text, _command_type, _widget_type, _widget_property, _property_value = self.command_stack.redo_command()
        _command = _widget_type
        if _command_type == 'colour':
            self.update_rendered_widget(widget_type=_widget_type,
                                        widget_property=_widget_property, property_value=_property_value)

        elif _command == 'set_appearance_mode':
            # _property_value is 'Light' or 'Dark'
            self.tk_seg_mode.set(_property_value + ' Mode')

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
            self.update_wip_file()
            self.load_theme_palette()
            self.render_widget_properties()

        elif _command_type == 'palette_colour':
            palette_button_id = _widget_property
            self.set_palette_colour(palette_button_id=palette_button_id, colour=_property_value)

        self.set_option_states()
        self.status_bar.set_status_text(
            status_text=redo_text)

    def update_wip_file(self):
        with open(self.wip_json, "w") as f:
            json.dump(self.theme_json_data, f, indent=2)

    def load_theme(self, event=None, reload_preview: bool = True):

        if self.json_state == 'dirty':
            confirm = CTkMessagebox(master=self,
                                    title='Confirm Action',
                                    message=f'You have unsaved changes. Are you sure you wish to proceed?',
                                    options=["Yes", "No"])
            response = confirm.get()
            if response == 'No':
                return
        selected_theme = self.opm_theme.get()

        if selected_theme == '-- Select Theme --':
            return

        self.status_bar.set_status_text(status_text=f'Opening theme, {selected_theme} ...')
        self.theme_file = selected_theme + '.json'
        self.source_json_file = self.theme_json_dir / self.theme_file
        if not self.source_json_file.exists():
            # Then likely that we are just starting up and last theme
            # opened was probably deleted.
            self.json_files = mod.user_themes_list()
            initial_display = mod.user_themes_list()
            self.opm_theme.configure(values=initial_display)
            self.opm_theme.set('-- Select Theme --')
            return

        if not self.source_json_file:
            return

        self.wip_json = self.TEMP_DIR / self.theme_file
        self.preview_json = self.TEMP_DIR / self.theme_file
        shutil.copyfile(self.source_json_file, self.wip_json)
        self.theme_json_data = mod.json_dict(json_file_path=self.wip_json)
        # The patch function checks to see if the theme, has wrong, pre CustomTkinter 5.2.0 property names.
        # If so, it patches up the theme JSON. These should be CTkCheckBox and CTkRadioButton.
        self.theme_json_data = mod.patch_theme(theme_json=self.theme_json_data)
        with open(self.wip_json, "w") as f:
            json.dump(self.theme_json_data, f, indent=2)

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
        self.opm_theme.configure(values=self.json_files)

        self.wip_palette_file = self.TEMP_DIR / self.theme_file.replace('json', 'tmpl')
        palette_file = selected_theme + '.json'
        self.theme = selected_theme
        self.source_palette_file = self.palettes_dir / palette_file
        if not self.source_palette_file.exists():
            self.create_theme_palette(selected_theme)
        shutil.copyfile(self.source_palette_file, self.wip_palette_file)
        # Force the Control Panel to complete rendering here,
        # otherwise if we are auto-loading the last theme at app startup,
        # the preview panel renders, before the Control Panel finishes - looks messy.
        self.update()
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
        self.json_state = 'clean'
        self.set_option_states()

    def save_harmonics_geometry(self):
        """Save the harmonics panel geometry to the repo, for the next time the dialog is launched."""
        geometry_row = mod.preference_row(db_file_path=DB_FILE_PATH,
                                          scope='window_geometry',
                                          preference_name='harmonics_panel')
        panel_geometry = self.geometry()
        geometry_row["preference_value"] = panel_geometry
        mod.upsert_preference(db_file_path=DB_FILE_PATH, preference_row_dict=geometry_row)

    def close_harmonics(self):
        self.rendered_keystone_shades.clear()
        self.save_harmonics_geometry()
        self.destroy()
        self.harmony_palette_running = False
        self.set_option_states()

    def restore_harmony_geometry(self):
        """Restore window geometry from auto-saved preferences"""
        saved_geometry = mod.preference_setting(db_file_path=DB_FILE_PATH,
                                                scope='window_geometry',
                                                preference_name='harmonics_panel')
        self.geometry(saved_geometry)
        self.resizable(False, False)

    def launch_harmony_dialog(self):
        harmonics_dialog = HarmonicsDialog(theme_name=self.theme,
                                           theme_json_data=self.theme_json_data)

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
            # Leverage the paste_palette_colour method to update the widget and the preview panel.
            self.paste_palette_colour(event=None, palette_button_id=palette_button_id)

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
        property_widget.configure(fg_color=darker_shade)
        if self.appearance_mode == 'Light':
            mode_idx = 0
        else:
            mode_idx = 1
        if darker_shade != widget_colour:
            pyperclip.copy(darker_shade)
            # Leverage the _paste_color method to update the widget and the preview panel.
            self.paste_colour(event=None, widget_property=widget_property)

    def load_theme_palette(self):
        """Determine and open the JSON theme palette file, for the selected theme, and marry the colours mapped in
        the file, to the palette widgets. """

        theme_name = self.theme_file
        palette_json = theme_name

        self.source_palette_file = self.palettes_dir / palette_json
        if not self.source_palette_file.exists():
            self.create_theme_palette(theme_name)

        self.wip_palette_file = self.TEMP_DIR / theme_name.replace('json', 'tmpl')

        if not self.source_palette_file.exists():
            self.create_theme_palette(theme_name)
        shutil.copyfile(self.source_palette_file, self.wip_palette_file)
        self.theme_palette = mod.json_dict(json_file_path=self.wip_palette_file)

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
        pass

    def reset_theme(self):
        """Reset the theme file, to the state of the last save operation, or the state when it was opened,
        if there has been no intervening save. """
        confirm = CTkMessagebox(master=self,
                                title='Confirm Action',
                                message=f'You have unsaved changes. Are you sure you wish to discard them?',
                                options=["Yes", "No"])
        if confirm.get() == 'No':
            return
        self.json_state = 'clean'
        # TODO: Remove this line below
        # self.load_theme_palette()
        self.load_theme()
        # Reset (empty) the undo/redo stacks
        self.command_stack.reset_stacks()
        self.set_option_states()

    def create_theme(self):
        """Create a new theme. This is based on the default_theme.json file."""
        if self.json_state == 'dirty':
            confirm = CTkMessagebox(master=self,
                                    title='Confirm Action',
                                    message=f'You have unsaved changes. Are you sure you wish to discard them?',
                                    options=["Yes", "No"])
            if confirm.get() == 'No':
                return
        source_file = ETC_DIR / 'default_theme.json'
        dialog = ctk.CTkInputDialog(text="Enter new theme name:", title="Create New Theme")
        new_theme = dialog.get_input()
        if new_theme:
            if not mod.valid_theme_file_name(new_theme):
                self.status_bar.set_status_text(
                    status_text=f'The entered theme name contains disallowed characters - allowed: alphanumeric, '
                                f'underscores & ()')
                return
            # If user has included a ".json" extension, remove it, because we add one below.
            new_theme_basename = os.path.splitext(new_theme)[0]
            new_theme = new_theme_basename + '.json'
            creanew_theme = new_theme_basename + '.json'
            new_theme_path = self.theme_json_dir / new_theme
            if new_theme_path.exists():
                self.status_bar.set_status_text(status_text=f'Theme {new_theme} already exists - '
                                                            f'please choose another name!')
                return
            shutil.copyfile(source_file, new_theme_path)
            self.json_files = mod.user_themes_list()
            self.opm_theme.configure(values=self.json_files)
            self.opm_theme.set(new_theme_basename)
            self.load_theme(reload_preview=False)
            self.theme_json_data['provenance']['theme name'] = new_theme_basename
            self.theme_json_data['provenance']['created with'] = f"CTk Theme Builder v{mod.app_version()}"
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
        confirm = CTkMessagebox(master=self,
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

        self.json_files = mod.user_themes_list()
        initial_display = mod.user_themes_list()
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
            if not mod.valid_theme_file_name(new_theme):
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
                self.theme_json_data['provenance']['created with'] = f"CTk Theme Builder v{mod.app_version()}"
            else:
                provenance = {"theme name": new_theme,
                              "theme author": theme_author,
                              "date created": date_saved_as,
                              "last modified by": theme_author,
                              "last modified": "Apr 26 2023 14:40:22",
                              "created with": f"CTk Theme Builder v{mod.app_version()}",
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
            source_palette_path = self.palettes_dir / self.source_palette_file
            self.palette_file = new_palette_path

            shutil.copyfile(source_palette_path, new_palette_path)

            self.save_theme()
            self.json_files = mod.user_themes_list()
            self.opm_theme.configure(values=self.json_files)
            self.theme = new_theme
            self.json_state = 'clean'
            self.command_stack.reset_stacks()
            self.set_option_states()

    def paste_colour(self, event, widget_property, property_colour: str = None):
        """Paste the colour currently stored in the paste buffer, to the selected button, where the paste operation
        was invoked. Note that we can circumvent the copy/paste process, by receiving the colour as a parameter."""
        if property_colour is None:
            new_colour = pyperclip.paste()
        else:
            new_colour = property_colour

        if not cbtk.valid_colour(new_colour):
            self.status_bar.set_status_text(status_text='Attempted paste of non colour code text - ignored.')
            return
        self.set_widget_colour(widget_property=widget_property, new_colour=new_colour)
        hover_colour = cbtk.contrast_colour(new_colour)
        # We don't know whether the widget is displayed for sure, when we are using cascade from the colour palette
        # region, so we need to check, the selected view, may not include the widget.
        if self.widgets[widget_property]['tile'].winfo_exists():
            self.widgets[widget_property]['tile'].configure(fg_color=new_colour, hover_color=hover_colour)

        # widget_type, base_property = mod.widget_property_split(widget_property=widget_property)
        if property_colour is None:
            self.status_bar.set_status_text(
                status_text=f'Colour {new_colour} assigned to widget property {widget_property}.')
        else:
            self.status_bar.set_status_text(
                status_text=f'Cascading colour {new_colour}, to associated widget properties...')

        if self.json_state != 'dirty':
            self.json_state = 'dirty'
            self.set_option_states()

    def paste_palette_colour(self, event, palette_button_id):

        new_colour = pyperclip.paste()
        if not cbtk.valid_colour(new_colour):
            self.status_bar.set_status_text(status_text='Attempted paste of non colour code - pasted text ignored.')
            return
        old_colour = self.theme_palette_tiles[palette_button_id].cget("fg_color")
        change_vector = mod.PropertyVector(command_type='palette_colour',
                                           command='null',
                                           component_type='palette_tile',
                                           component_property=palette_button_id,
                                           new_value=new_colour,
                                           old_value=old_colour)
        self.command_stack.exec_command(property_vector=change_vector)

        self.set_palette_colour(palette_button_id=palette_button_id, colour=new_colour)

        self.json_state = 'dirty'
        self.set_option_states()
        self.status_bar.set_status_text(
            status_text=f'Colour {new_colour} assigned to palette entry {palette_button_id + 1}.')

    def set_palette_colour(self, palette_button_id, colour):
        hover_colour = cbtk.contrast_colour(colour)
        self.theme_palette_tiles[palette_button_id].configure(fg_color=colour, hover_color=hover_colour)
        self.json_state = 'dirty'
        self.set_option_states()

    def set_filtered_widget_display(self, dummy='dummy'):
        self.render_widget_properties()

    def property_colour_picker(self, event, widget_property):
        prev_colour = self.widgets[widget_property]["colour"]
        new_colour = askcolor(master=self, title='Pick colour for : ' + widget_property,
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
            old_colour = self.theme_palette_tiles[palette_button_id].cget("fg_color")
            change_vector = mod.PropertyVector(command_type='palette_colour',
                                               command='null',
                                               component_type='palette_tile',
                                               component_property=palette_button_id,
                                               new_value=new_colour,
                                               old_value=old_colour)
            self.command_stack.exec_command(property_vector=change_vector)

            self.set_palette_colour(palette_button_id=palette_button_id, colour=new_colour)

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
        # TODO: Performance investigation here

        # start_time = time.time()

        filter_key = self.opm_properties_filter.get()

        # end_time = time.time()
        # elapsed_time = end_time - start_time
        # print("Elapsed time 1: ", elapsed_time)
        self.filter_list = self.widget_attributes[filter_key]
        # self.appearance_mode = self.seg_mode.get()

        widget_frame = self.frm_colour_edit_widgets

        # The colours dictionary here is composed of a composite key and colour value.
        # The key consists of the display widget type ('CTk' string removed excepting for the CTk() widget).
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
            btn_property = entry['tile']
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
                    # json_widget_type = mod.json_widget_type(widget_type=widget_type)
                    colour_value = self.theme_json_data[widget_type][widget_property]
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

                self.widgets[key] = {"tile": btn_property, 'label': lbl_property, 'widget_type': widget_type,
                                     'widget_property': widget_property, 'colour': colour}
                # Set a binding so that we can paste a colour, previously copied into our clipboard
                if self.enable_single_click_paste and colour_value != "transparent":
                    self.widgets[key]['tile'].bind("<Button-1>",
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
                    context_menu = cbtk.CBtkMenu(self.widgets[key]['tile'], tearoff=False)
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
                                              command=lambda widget=btn_property, wgt_type=widget_type,
                                                             wgt_property=key:
                                              self.lighten_widget_property_shade(property_widget=widget,
                                                                                 widget_property=wgt_property,
                                                                                 shade_step=self.shade_adjust_differential,
                                                                                 multiplier=1))

                    shade_up_menu.add_command(label="Lighter x 2", state="normal",
                                              command=lambda widget=btn_property, wgt_type=widget_type,
                                                             wgt_property=key:
                                              self.lighten_widget_property_shade(property_widget=widget,
                                                                                 widget_property=wgt_property,
                                                                                 shade_step=self.shade_adjust_differential,
                                                                                 multiplier=2))

                    shade_up_menu.add_command(label="Lighter x 3", state="normal",
                                              command=lambda widget=btn_property, wgt_type=widget_type,
                                                             wgt_property=key:
                                              self.lighten_widget_property_shade(property_widget=widget,
                                                                                 widget_property=wgt_property,
                                                                                 shade_step=self.shade_adjust_differential,
                                                                                 multiplier=3))

                    shade_down_menu = cbtk.CBtkMenu(context_menu, tearoff=False)
                    shade_down_menu.add_command(label="Darker", state="normal",
                                                command=lambda widget=btn_property, wgt_type=widget_type,
                                                               wgt_property=key:
                                                self.darken_widget_property_shade(property_widget=widget,
                                                                                  widget_property=wgt_property,
                                                                                  shade_step=self.shade_adjust_differential,
                                                                                  multiplier=1))

                    shade_down_menu.add_command(label="Darker x 2", state="normal",
                                                command=lambda widget=btn_property, wgt_type=widget_type,
                                                               wgt_property=key:
                                                self.darken_widget_property_shade(property_widget=widget,
                                                                                  widget_property=wgt_property,
                                                                                  shade_step=self.shade_adjust_differential,
                                                                                  multiplier=2))

                    shade_down_menu.add_command(label="Darker x 3", state="normal",
                                                command=lambda widget=btn_property, wgt_type=widget_type,
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
                    self.widgets[key]['tile'].bind("<Button-3>",
                                                   lambda event, menu=context_menu, button_id=btn_idx:
                                                   self.context_menu(event, menu))

                    btn_idx += 1

    def update_rendered_widget(self, widget_type, widget_property, property_value):
        composite_property = mod.PropertyVector.display_property(widget_type=widget_type,
                                                                 widget_property=widget_property)
        for widget_record in self.widgets.values():
            _widget_type = widget_record["widget_type"]
            _widget_property = widget_record["widget_property"]
            _display_tile = widget_record["tile"]
            appearance_mode_index = cbtk.str_mode_to_int(self.appearance_mode)
            self.theme_json_data[widget_type][widget_property][appearance_mode_index] = property_value

            if widget_type == _widget_type and widget_property == _widget_property:
                if _display_tile.winfo_exists():
                    _display_tile.configure(fg_color=property_value)

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

        confirm = CTkMessagebox(master=self,
                                title='Confirm Action',
                                message=f'This will replace the theme\'s "{to_mode_description}" mode settings with '
                                        f'those from the "{current_mode}" configuration.',
                                options=["Yes", "No"])
        if confirm.get() == 'Cancel':
            return
        counter = 0
        for property_id in self.filter_list:
            widget_type, widget_property = mod.widget_property_split(property_id)
            # json_widget_type = mod.json_widget_type(widget_type=widget_type)
            json_widget_type = widget_type
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

        confirm = CTkMessagebox(master=self,
                                title='Confirm Action',
                                message=f'This will replace the Theme Palette colours for the theme\'s '
                                        f'"{to_mode_description}" mode settings with '
                                        f'those from the "{current_mode}" mode.',
                                options=["Yes", "No"])
        if confirm.get() == 'Cancel':
            return

        self.sync_palette_mode_colours()
        self.stash_theme_palette(mode=from_mode)
        self.load_stashed_theme_palette(to_mode)
        self.json_state = 'dirty'
        self.set_option_states()

    def refresh_preview(self, set_scaling: bool=True):
        """The _refresh_preview method, instructs the Preview Panel to perform a re-rendering of all widgets."""

        self.update_wip_file()
        mod.send_command_json(command_type='program',
                              command='refresh',
                              parameters=[self.appearance_mode])

        if set_scaling:
            mod.send_command_json(command_type='program',
                                  command='set_widget_scaling',
                                  parameters=[self.preview_panel_scaling_pct])

    def reload_preview(self):
        """The reload_preview method causes a full reload of the preview panel."""
        if self.process:
            mod.send_command_json(command_type='program',
                                  command='quit',
                                  parameters=None)

        self.update_wip_file()

        self.process = None

        self.launch_preview()
        if self.tk_render_disabled.get():
            mod.send_command_json(command_type='program',
                                  command='render_preview_disabled',
                                  parameters=None)
        else:
            mod.send_command_json(command_type='program',
                                  command='render_preview_enabled',
                                  parameters=None)

        frame_mode = self.tk_swt_frame_mode.get()
        if frame_mode == 'base':
            mod.send_command_json(command_type='program', command='render_base_frame')

    def close_panels(self, event=None):
        if self.json_state == 'dirty':
            confirm = CTkMessagebox(master=self,
                                    title='Confirm Action',
                                    message=f'You have unsaved changes. Do you wish to save these before quitting?',
                                    options=["Yes", "No", "Cancel"])
            response = confirm.get()
            if response == 'Cancel':
                return
            elif response == 'Yes':
                self.save_theme()

        if self.qa_launched:
            mod.request_close_qa_app()
        if self.process:
            mod.send_command_json(command_type='program',
                                  command='quit',
                                  parameters=None)

        self.save_controller_geometry()
        self.destroy()

    def launch_preview(self):
        # We need to temporarily disable the window close widget,
        # until the preview panel is loaded, and redy for commands.
        self.protocol("WM_DELETE_WINDOW", self.block_window_close)
        appearance_mode_ = self.appearance_mode
        self.update_wip_file()

        designer = str(APP_HOME / 'ctk_theme_builder.py')
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
                    confirm = CTkMessagebox(master=self,
                                            title='Please Upgrade CustomTkinter',
                                            message=f'TIMEOUT: Waited too long for preview listener!\n\n'
                                                    f'Ensure that only one instance of {mod.app_title()} is running is '
                                                    f'running on port {self.listener_port}, and that no other process '
                                                    f'is using the port.',
                                            option_1='OK')
                    print('ERROR: Waited too long for listener!')
                    print(f'       Ensure that only one instance of {mod.app_title()} is running.')
                    if confirm.get() == 'OK':
                        exit(1)
                time.sleep(0.1)

            # Update the listener address here, just in case there has been a port change via preferences.
            self.method_listener_address = mod.method_listener_address()
            mod.send_command_json(command_type='program',
                                  command='set_widget_scaling',
                                  parameters=[self.preview_panel_scaling_pct])

        self.protocol("WM_DELETE_WINDOW", self.close_panels)

    def restore_controller_geometry(self):
        controller_geometry = mod.preference_setting(db_file_path=DB_FILE_PATH,
                                                     scope='window_geometry',
                                                     preference_name='control_panel')
        self.geometry(controller_geometry)
        # self.resizable(False, True)

    def save_controller_geometry(self):
        """Save the control panel geometry to the repo, for the next time the program is launched."""
        geometry_row = mod.preference_row(db_file_path=DB_FILE_PATH,
                                          scope='window_geometry',
                                          preference_name='control_panel')
        panel_geometry = self.geometry()
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

        self.update_wip_file()
        shutil.copyfile(self.wip_json, self.source_json_file)
        theme_file_name = os.path.basename(self.source_json_file)
        self.json_state = 'clean'

        self.status_bar.set_status_text(status_text=f'Theme file, {theme_file_name}, saved successfully!')
        self.command_stack.reset_stacks()
        self.set_option_states()
        self.save_theme_palette()

