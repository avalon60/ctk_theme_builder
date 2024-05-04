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
from CTkMessagebox import CTkMessagebox

APP_THEMES_DIR = mod.APP_THEMES_DIR
APP_IMAGES = mod.APP_IMAGES
DB_FILE_PATH = mod.DB_FILE_PATH


class Exporter(ctk.CTkToplevel):
    """This class is used to merge two themes, to create an entirely new theme."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.theme_pathname = pref.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                      preference_name='theme_json_dir')
        self.enable_tooltips = pref.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                       preference_name='enable_tooltips')

        self.open_when_merged = 0

        self.master = self.master
        self.title('Export Theme')
        self.geometry('400x150')

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
        btn_close = ctk.CTkButton(master=frm_buttons, text='Close', command=self.close_dialog)
        btn_close.grid(row=0, column=0, padx=(15, 35), pady=5)

        self.btn_export = ctk.CTkButton(master=frm_buttons, text="Export", command=self.export_theme, state=ctk.DISABLED)
        self.btn_export.grid(row=0, column=1, padx=(120, 15), pady=5)

        self.status_bar = cbtk.CBtkStatusBar(master=self,
                                             status_text_life=30,
                                             use_grid=True)
        self.bind("<Configure>", self.status_bar.auto_size_status_bar)
        position_child_widget(parent_widget=self.master, child_widget=self, y_offset=0.2)
        # self.get_export_directory()
        self.geometry("425x200")
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

        shutil.copyfile(self.theme_pathname / theme, export_theme_path)
        self.status_bar.set_status_text(status_text=f"Theme exported: {export_theme_path}")

    @log_call
    def get_export_directory(self, event):
        """The get_export_directory() method, determines where the theme file should be exported to. It determines
        the default downloads location, based on operating system, and initially assumes that location for exports.
        If the user navigates to a new location, this is remembered in case another theme is exported, within the same
        dialogue session, thereby becoming a temporary default."""

        # Open a file dialog to select a directory

        home_dir = None
        os_name = os_attribute("os_name")
        if os_name in ["Linux", "MacOS"]:
            home_dir = Path(os.environ.get("HOME"))
        elif os_name == "Windows" and os.environ.get("HOMEPATH") is not None:
            home_dir = Path(os.environ.get("HOMEPATH"))
        elif os_name == "Windows" and os.environ.get("USERPROFILE") is not None:
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

        self.btn_export.configure(state=ctk.NORMAL)
        self.download_directory = Path(download_directory)



class Importer(ctk.CTkToplevel):
    """This class is used to merge two themes, to create an entirely new theme."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.theme_json_dir = pref.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                      preference_name='theme_json_dir')
        self.enable_tooltips = pref.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                       preference_name='enable_tooltips')

        self.open_when_merged = 0

        self.master = self.master
        self.title('Import Theme')
        self.geometry('350x150')

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.columnconfigure(0, weight=1)
        self.os_name = os_attribute("os_name")

        self.import_directory = None
        self.default_import_dir = self.default_import_directory()
        self.theme_import_path = None


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

        self.folder_image = cbtk.load_image(light_image=APP_IMAGES / 'folder.png', image_size=(20, 20))
        lbl_theme_pathname = ctk.CTkLabel(master=frm_widgets, text='Select theme', justify="right")
        lbl_theme_pathname.grid(row=widget_start_row, column=0, padx=5, pady=(15, 5), sticky='e')

        if self.enable_tooltips:
            lbl_theme_pathname_tooltip = CTkToolTip(lbl_theme_pathname,
                                                    border_width=1,
                                                    justify="left",
                                                    padding=(10, 10),
                                                    corner_radius=6,
                                                    message="Select a theme file to import.")

        btn_theme_pathname = ctk.CTkButton(master=frm_widgets,
                                           text='',
                                           width=30,
                                           height=30,
                                           fg_color='#748696',
                                           image=self.folder_image,
                                           command=self.ask_theme_location)
        btn_theme_pathname.grid(row=widget_start_row, column=1, pady=(10, 0), sticky='w')
        widget_start_row += 1

        if self.enable_tooltips:
            CTkToolTip(btn_theme_pathname,
                       wraplength=250,
                       justify="left",
                       border_width=1,
                       padding=(10, 10),
                       corner_radius=6,
                       message="Select the theme you wish to import.")

        self.lbl_selected_theme_path = ctk.CTkLabel(master=frm_widgets, text="", justify="left",
                                                    font=mod.REGULAR_TEXT)
        self.lbl_selected_theme_path.grid(row=widget_start_row, column=1, columnspan=5, padx=5, pady=5, sticky='w')



        widget_start_row += 1

        # Control buttons
        btn_close = ctk.CTkButton(master=frm_buttons, text='Close', command=self.close_dialog)
        btn_close.grid(row=0, column=0, padx=(15, 35), pady=5)

        self.btn_import = ctk.CTkButton(master=frm_buttons, text='Import', command=self.import_theme, state=ctk.DISABLED)
        self.btn_import.grid(row=0, column=1, padx=(15, 15), pady=5)

        self.status_bar = cbtk.CBtkStatusBar(master=self,
                                             status_text_life=30,
                                             use_grid=True)
        self.bind("<Configure>", self.status_bar.auto_size_status_bar)
        position_child_widget(parent_widget=self.master, child_widget=self, y_offset=0.2)

        self.geometry("325x200")
        self.grab_set()
        self.lift()
        self.bind('<Escape>', self.close_dialog)

    @log_call
    def close_dialog(self):
        log.log_debug(log_text='Theme merger dialogue cancelled', class_name='ThemeMerger', method_name='close_dialog')
        self.destroy()

    def ask_theme_location(self, event=None):
        # Set file types to only show JSON files
        filetypes = [("JSON Files", "*.json")]
        theme_file = filedialog.askopenfilename(initialdir=self.default_import_dir,
                                                title="Select a Theme File",
                                                filetypes=filetypes)
        if not theme_file:
            return

        self.default_import_dir = Path(theme_file).parent
        self.lbl_selected_theme_path.configure(text=theme_file)
        self.btn_import.configure(state=ctk.NORMAL)
        self.theme_import_path = Path(theme_file)

    @log_call
    def import_theme(self):

        theme = self.theme_import_path.name.rsplit('.', 1)[0]  # Remove file extension
        theme_json = self.theme_import_path.name

        target_file = self.theme_json_dir / theme_json
        print(f"target_file: {target_file}")
        if target_file.exists():
            confirm = CTkMessagebox(master=self,
                                    title='Confirm Action',
                                    message=f'A theme with that name already exists in your repository, and will be '
                                            f'overwritten. Are you sure you wish to proceed?',
                                    options=["Yes", "No"])
            response = confirm.get()
            if response == 'No':
                return

        shutil.copyfile(self.theme_import_path, self.theme_json_dir / theme_json)
        self.status_bar.set_status_text(status_text=f"Theme imported: {theme}")
        self.master.json_files = mod.user_themes_list()
        self.master.opm_theme.configure(values=self.master.json_files)

    @log_call
    def default_import_directory(self, event=None):
        """The default_import_directory() method, determines where the theme file should be exported to. It determines
        the default downloads location, based on operating system, and initially assumes that location for imports.
        If the user navigates to a new location, this is remembered in case another theme is imported, within the same
        dialogue session, thereby becoming a temporary default."""

        home_dir = None
        os_name = os_attribute("os_name")
        if os_name in ["Linux", "MacOS"]:
            home_dir = Path(os.environ.get("HOME"))
        elif os_name == "Windows" and os.environ.get("HOMEPATH") is not None:
            home_dir = Path(os.environ.get("HOMEPATH"))
        elif os_name == "Windows" and os.environ.get("USERPROFILE") is not None:
            home_dir = Path(os.environ.get("USERPROFILE"))

        if not home_dir.exists():
            home_dir = "/"

        # If user has already selected a download directory, default to that...
        if self.import_directory:
            download_dir = self.import_directory
        else:
            download_dir = home_dir / "Downloads"

        if not download_dir.exists():
            download_dir = home_dir

        self.download_directory = Path(download_dir)
        return self.download_directory
