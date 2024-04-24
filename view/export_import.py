"""Class container for CTk Theme Builder theme merger dialogue."""

import model.ctk_theme_builder as mod
from model.ctk_theme_builder import log_call
from model.ctk_theme_builder import os_attribute
import customtkinter as ctk
import tkinter as tk
import os
from CTkToolTip import *
import utils.cbtk_kit as cbtk
import model.preferences as pref
import utils.loggerutl as log
from tkinter import filedialog
from pathlib import Path
from view.view_utils import position_child_widget
import shutil


APP_THEMES_DIR = mod.APP_THEMES_DIR
APP_IMAGES = mod.APP_IMAGES
DB_FILE_PATH = mod.DB_FILE_PATH


class Exporter(ctk.CTkToplevel):
    """This class is used to merge two themes, to create an entirely new theme."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.theme_json_dir = pref.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                      preference_name='theme_json_dir')
        self.enable_tooltips = pref.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                       preference_name='enable_tooltips')

        self.open_when_merged = 0

        self.master = self.master
        self.title('Export Theme')
        self.geometry('350x150')

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.columnconfigure(0, weight=1)
        self.os_name = os_attribute("os_name")
        self.download_directory = None

        frm_main = ctk.CTkFrame(master=self, corner_radius=10)
        frm_main.grid(column=0, row=0, sticky='nsew')
        frm_main.columnconfigure(0, weight=1)
        frm_main.rowconfigure(0, weight=1)

        frm_main = ctk.CTkFrame(master=self, corner_radius=10)
        frm_main.grid(column=0, row=0, sticky='nsew')
        frm_main.columnconfigure(0, weight=1)
        frm_main.rowconfigure(0, weight=1)

        frm_widgets = ctk.CTkFrame(master=frm_main, corner_radius=10)
        frm_widgets.grid(column=0, row=0, padx=5, pady=5, sticky='nsew')

        frm_buttons = ctk.CTkFrame(master=frm_main, corner_radius=0)
        frm_buttons.grid(column=0, row=1, padx=0, pady=(0, 0), sticky='ew')

        widget_start_row = 0

        lbl_export_theme = ctk.CTkLabel(master=frm_widgets, text='Theme', justify="right")
        lbl_export_theme.grid(row=widget_start_row, column=0, padx=15, pady=(20, 5), sticky='e')

        if self.enable_tooltips:
            lbl_export_theme_tooltip = CTkToolTip(lbl_export_theme,
                                                  wraplength=250,
                                                  justify="left",
                                                  border_width=1,
                                                  padding=(10, 10),
                                                  corner_radius=6,
                                                  message="Select the theme you wish to export.")

        self.tk_export_theme = ctk.StringVar()
        self.tk_export_theme.set("-- Select Theme --")
        self.opm_export_theme = ctk.CTkOptionMenu(master=frm_widgets,
                                                  variable=self.tk_export_theme,
                                                  command=self.get_export_directory,
                                                  values=mod.user_themes_list())
        self.opm_export_theme.grid(row=widget_start_row, column=1, padx=(0, 10), pady=(20, 5), sticky='w')

        widget_start_row += 1

        # Control buttons
        btn_close = ctk.CTkButton(master=frm_buttons, text='Cancel', command=self.close_dialog)
        btn_close.grid(row=0, column=0, padx=(15, 35), pady=5)

        btn_export = ctk.CTkButton(master=frm_buttons, text='Export', command=self.export_theme)
        btn_export.grid(row=0, column=1, padx=(15, 15), pady=5)

        self.status_bar = cbtk.CBtkStatusBar(master=self,
                                             status_text_life=30,
                                             use_grid=True)
        self.bind("<Configure>", self.status_bar.auto_size_status_bar)
        position_child_widget(parent_widget=self.master, child_widget=self, y_offset=0.2)
        # self.get_export_directory()
        self.grab_set()
        self.lift()
        self.bind('<Escape>', self.close_dialog)


    @log_call
    def close_dialog(self):
        log.log_debug(log_text='Theme merger dialogue cancelled', class_name='ThemeMerger', method_name='close_dialog')
        self.destroy()

    @log_call
    def export_theme(self):
        export_directory = self.download_directory

        theme = self.tk_export_theme.get() + ".json"
        export_theme_path = export_directory / theme

        shutil.copyfile(self.theme_json_dir / theme, export_theme_path)
        self.status_bar.set_status_text(status_text=f"Exported: {export_theme_path}")

    @log_call
    def get_export_directory(self, event):
        """The get_export_directory() method, determines where the theme file should be exported to. It determines
        the default downloads location, based on operating system, and initially assumes that location for exports.
        If the user navigates to a new location, this is remembered in case another theme is exported, within the same
        dialogue session, becoming a temporary default."""

        # Open a file dialog to select a directory

        home_dir = None
        os_name = os_attribute("os_name")
        if os_name in ["Linux", "MacOS"]:
            home_dir = Path(os.environ.get("HOME"))
        elif os_name == "Windows" and os.environ.get("HOMEPATH") is not None:
            home_dir = Path(os.environ.get("HOMEPATH"))
        elif os_name == "Windows" and os.environ.get("USERPROFILE")is not None:
            home_dir = Path(os.environ.get("USERPROFILE"))

        if not home_dir.exists():
            home_dir = "/"

        # If user has already selected a download directory, default to that...
        if self.download_directory:
            download_dir = self.download_directory
        else:
            download_dir = home_dir / "Downloads"

        if not download_dir.exists():
            download_dir = home_dir
        select = True
        if select:
            download_directory = filedialog.askdirectory(initialdir=download_dir)
            if not download_directory:
                download_directory = download_dir
        else:
            download_directory = download_dir
        print("Selected directory:", download_directory)
        self.download_directory = Path(download_directory)
        # Print the selected directory


class Importer(ctk.CTkToplevel):
    """This class is used to merge two themes, to create an entirely new theme."""

    @log_call
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.theme_json_dir = pref.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                      preference_name='theme_json_dir')
        self.enable_tooltips = pref.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                       preference_name='enable_tooltips')
        self.open_when_merged = 0

        self.master = self.master
        self.title('Export Theme')
        # self.geometry('760x350')

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.columnconfigure(0, weight=1)

        frm_main = ctk.CTkFrame(master=self, corner_radius=10)
        frm_main.grid(column=0, row=0, sticky='nsew')
        frm_main.columnconfigure(0, weight=1)
        frm_main.rowconfigure(0, weight=1)

        frm_main = ctk.CTkFrame(master=self, corner_radius=10)
        frm_main.grid(column=0, row=0, sticky='nsew')
        frm_main.columnconfigure(0, weight=1)
        frm_main.rowconfigure(0, weight=1)

        frm_widgets = ctk.CTkFrame(master=frm_main, corner_radius=10)
        frm_widgets.grid(column=0, row=0, padx=5, pady=5, sticky='nsew')

        frm_buttons = ctk.CTkFrame(master=frm_main, corner_radius=0)
        frm_buttons.grid(column=0, row=1, padx=0, pady=(0, 0), sticky='ew')

        widget_start_row = 0

        lbl_export_theme = ctk.CTkLabel(master=frm_widgets, text='Theme', justify="right")
        lbl_export_theme.grid(row=widget_start_row, column=0, padx=5, pady=(20, 5), sticky='e')

        self.master.update_idletasks()

        if self.enable_tooltips:
            lbl_export_theme_tooltip = CTkToolTip(lbl_export_theme,
                                                  wraplength=250,
                                                  justify="left",
                                                  border_width=1,
                                                  padding=(10, 10),
                                                  corner_radius=6,
                                                  message="Select the theme you wish to export.")

        self.tk_export_theme = tk.StringVar()
        self.opm_export_theme = ctk.CTkOptionMenu(master=frm_widgets,
                                                  variable=self.tk_export_theme,
                                                  values=mod.user_themes_list())
        self.opm_export_theme.grid(row=widget_start_row, column=1, padx=(0, 10), pady=(20, 5), sticky='w')

        lbl_primary_mode = ctk.CTkLabel(master=frm_widgets, text='Appearance mode', justify="right")
        lbl_primary_mode.grid(row=widget_start_row, column=2, padx=5, pady=(20, 5), sticky='e')
        if self.enable_tooltips:
            btn_author_tooltip = CTkToolTip(lbl_primary_mode,
                                            wraplength=250,
                                            justify="left",
                                            border_width=1,
                                            padding=(10, 10),
                                            corner_radius=6,
                                            message="Select the appearance mode to be merged from the primary theme.")
        # The export_theme_mode holds the CustomTkinter appearance mode (Dark / Light)
        self.tk_primary_mode = tk.StringVar()
        rdo_primary_light = ctk.CTkRadioButton(master=frm_widgets, text='Light',
                                               variable=self.tk_primary_mode,
                                               value='Light')
        rdo_primary_light.grid(row=widget_start_row, column=3, pady=(20, 5), sticky='w')
        widget_start_row += 1

        rdo_primary_dark = ctk.CTkRadioButton(master=frm_widgets, text='Dark', variable=self.tk_primary_mode,
                                              value='Dark')
        rdo_primary_dark.grid(row=widget_start_row, column=3, pady=5, sticky='w')

        rdo_primary_dark.deselect()
        rdo_primary_light.select()

        # We need to determine where the primary theme's appearance mode will be mapped to.
        widget_start_row = 0
        lbl_primary_mapped_mode = ctk.CTkLabel(master=frm_widgets, text='Map primary mode to', justify="right")
        lbl_primary_mapped_mode.grid(row=widget_start_row, column=4, padx=5, pady=(20, 5), sticky='e')
        if self.enable_tooltips:
            btn_author_tooltip = CTkToolTip(lbl_primary_mapped_mode,
                                            wraplength=250,
                                            justify="left",
                                            border_width=1,
                                            padding=(10, 10),
                                            corner_radius=6,
                                            message="Select which appearance mode, the selected primary mode will be"
                                                    " mapped to. \n\nThe secondary theme's selected appearance mode, "
                                                    "will be mapped to the unselected mode.")
        self.tk_primary_mapped_mode = tk.StringVar()
        rdo_primary_mapped_light = ctk.CTkRadioButton(master=frm_widgets, text='Light',
                                                      variable=self.tk_primary_mapped_mode,
                                                      value='Light')
        rdo_primary_mapped_light.grid(row=widget_start_row, column=5, pady=(20, 5), sticky='w')
        widget_start_row += 1

        rdo_primary_mapped_dark = ctk.CTkRadioButton(master=frm_widgets, text='Dark',
                                                     variable=self.tk_primary_mapped_mode,
                                                     value='Dark')
        rdo_primary_mapped_dark.grid(row=widget_start_row, column=5, pady=5, sticky='w')

        rdo_primary_mapped_dark.deselect()
        rdo_primary_mapped_light.select()

        widget_start_row += 1

        lbl_secondary_theme = ctk.CTkLabel(master=frm_widgets, text='Secondary theme', justify="right")
        lbl_secondary_theme.grid(row=widget_start_row, column=0, padx=5, pady=(20, 5), sticky='e')

        if self.enable_tooltips:
            btn_author_tooltip = CTkToolTip(lbl_secondary_theme,
                                            wraplength=250,
                                            justify="left",
                                            border_width=1,
                                            padding=(10, 10),
                                            corner_radius=6,
                                            message="The secondary theme to merge. The non-colour properties are, "
                                                    "adopted from the secondary theme.")

        self.tk_secondary_theme = tk.StringVar()
        self.opm_secondary_theme = ctk.CTkOptionMenu(master=frm_widgets,
                                                     variable=self.tk_secondary_theme,
                                                     values=mod.user_themes_list())
        self.opm_secondary_theme.grid(row=widget_start_row, column=1, padx=(0, 10), pady=(20, 5), sticky='w')

        lbl_secondary_mode = ctk.CTkLabel(master=frm_widgets, text='Appearance mode', justify="right")
        lbl_secondary_mode.grid(row=widget_start_row, column=2, padx=5, pady=(20, 5), sticky='e')
        if self.enable_tooltips:
            btn_author_tooltip = CTkToolTip(lbl_secondary_mode,
                                            wraplength=250,
                                            justify="left",
                                            border_width=1,
                                            padding=(10, 10),
                                            corner_radius=6,
                                            message="Select the appearance mode to be merged from the secondary theme.")
        # The secondary_theme_mode holds the CustomTkinter appearance mode (Dark / Light)
        self.tk_secondary_mode = tk.StringVar()
        rdo_secondary_light = ctk.CTkRadioButton(master=frm_widgets, text='Light',
                                                 variable=self.tk_secondary_mode,
                                                 value='Light')
        rdo_secondary_light.grid(row=widget_start_row, column=3, pady=(20, 5), sticky='w')
        widget_start_row += 1

        rdo_secondary_dark = ctk.CTkRadioButton(master=frm_widgets, text='Dark',
                                                variable=self.tk_secondary_mode,
                                                value='Dark')
        rdo_secondary_dark.grid(row=widget_start_row, column=3, pady=5, sticky='w')

        rdo_secondary_dark.deselect()
        rdo_secondary_light.select()

        widget_start_row += 1
        lbl_new_theme_name = ctk.CTkLabel(master=frm_widgets, text='New theme name', justify="right")
        lbl_new_theme_name.grid(row=widget_start_row, column=0, padx=10, pady=(30, 20), sticky='e')

        if self.enable_tooltips:
            btn_author_tooltip = CTkToolTip(lbl_new_theme_name,
                                            wraplength=250,
                                            justify="left",
                                            border_width=1,
                                            padding=(10, 10),
                                            corner_radius=6,
                                            message="Provide a new target theme file name.")

        self.tk_new_theme_file = tk.StringVar()
        self.ent_new_theme_file = ctk.CTkEntry(master=frm_widgets,
                                               textvariable=self.tk_new_theme_file,
                                               width=160)
        self.ent_new_theme_file.grid(row=widget_start_row, column=1, padx=(0, 0), pady=(30, 20), sticky='w')

        self.tk_open_on_merge = tk.IntVar(master=frm_widgets, value=0)
        self.swt_open_on_merge = ctk.CTkSwitch(master=frm_widgets,
                                               text='Open on merge',
                                               offvalue=0,
                                               onvalue=1,
                                               variable=self.tk_open_on_merge)
        self.swt_open_on_merge.grid(row=widget_start_row, column=3, padx=(0, 0), pady=(30, 20), sticky='w')

        if self.enable_tooltips:
            btn_enable_tooltips_tooltip = CTkToolTip(self.swt_open_on_merge,
                                                     wraplength=400,
                                                     justify="left",
                                                     border_width=1,
                                                     padding=(10, 10),
                                                     corner_radius=6,
                                                     message="Enable this switch, if you wish to open the merged theme.")

        widget_start_row += 1

        # Control buttons
        btn_close = ctk.CTkButton(master=frm_buttons, text='Cancel', command=self.close_dialog)
        btn_close.grid(row=0, column=0, padx=(15, 35), pady=5)

        btn_merge = ctk.CTkButton(master=frm_buttons, text='Merge', command=self.validate_and_import)
        btn_merge.grid(row=0, column=1, padx=(450, 15), pady=5)

        self.status_bar = cbtk.CBtkStatusBar(master=self,
                                             status_text_life=30,
                                             use_grid=True)
        self.bind("<Configure>", self.status_bar.auto_size_status_bar)

        self.grab_set()
        self.lift()
        self.bind('<Escape>', self.close_dialog)

    @log_call
    def close_dialog(self, event=None):
        log.log_debug(log_text='Theme merger dialogue cancelled', class_name='ThemeMerger', method_name='close_dialog')
        self.destroy()


    @log_call
    def validate_and_import(self):
        """This method processes the "Merge Themes" dialog (launch_merge_dialog) submission, and is activated by the
        Merge button."""
        log.log_debug(log_text='Validate theme inputs and merge',
                      class_name='ThemeMerger',
                      method_name='validate_and_merge')
        export_theme_name = self.tk_export_theme.get()

        primary_appearance_mode = self.tk_primary_mode.get()
        secondary_theme_name = self.tk_secondary_theme.get()
        secondary_appearance_mode = self.tk_secondary_mode.get()
        new_theme_file = self.tk_new_theme_file.get()
        open_on_merge = self.tk_open_on_merge.get()

        self.open_when_merged = None
        self.new_theme = None

        if not export_theme_name:
            self.status_bar.set_status_text('You must select a Primary theme name.')
            log.log_debug(log_text='VALIDATION: You must select a Primary theme name',
                          class_name='ThemeMerger',
                          method_name='validate_and_merge')
            return

        if not secondary_theme_name:
            self.status_bar.set_status_text('You must select a Secondary theme name.')
            log.log_debug(log_text='VALIDATION: You must select a Secondary theme name',
                          class_name='ThemeMerger',
                          method_name='validate_and_merge')
            return

        if export_theme_name == secondary_theme_name and primary_appearance_mode == secondary_appearance_mode:
            self.status_bar.set_status_text('You cannot merge the same theme / appearance mode to itself.')
            log.log_debug(log_text='VALIDATION: You cannot merge the same theme / appearance mode to itself',
                          class_name='ThemeMerger',
                          method_name='validate_and_merge')
            return

        if not mod.valid_theme_file_name(new_theme_file):
            self.status_bar.set_status_text('Invalid characters in new theme file name!')
            log.log_debug(log_text='VALIDATION: Invalid characters in new theme file name!',
                          class_name='ThemeMerger',
                          method_name='validate_and_merge')
            return

        if len(new_theme_file) == 0:
            self.status_bar.set_status_text(status_text=f'You must enter a theme name for the new theme.')
            return
        # If user has included a ".json" extension, remove it, because we add one below.
        new_theme_name = new_theme_basename = os.path.splitext(new_theme_file)[0]
        new_theme = new_theme_basename + '.json'
        new_theme_path = self.theme_json_dir / new_theme
        if new_theme_path.exists():
            self.status_bar.set_status_text(status_text=f'Theme file, {new_theme}, already exists - '
                                                        f'please choose another name!')
            return
        self.status_bar.set_status_text(status_text=f'Creating theme, {new_theme_name}, from {export_theme_name} '
                                                    f' and {secondary_theme_name}.')
        mod.merge_themes(export_theme_name=export_theme_name, primary_mode=primary_appearance_mode,
                         secondary_theme_name=secondary_theme_name, secondary_mode=secondary_appearance_mode,
                         new_theme_name=new_theme)

