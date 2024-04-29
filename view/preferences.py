"""Class container for the Preferences dialogue."""

import model.ctk_theme_builder as mod
from model.ctk_theme_builder import log_call
import customtkinter as ctk
import tkinter as tk
import platform
import os
from CTkToolTip import *
import utils.cbtk_kit as cbtk
import utils.loggerutl as log
from pathlib import Path
import model.preferences as pref
import utils.loggerutl as logutl
from CTkMessagebox import CTkMessagebox

APP_THEMES_DIR = mod.APP_THEMES_DIR
APP_IMAGES = mod.APP_IMAGES
DB_FILE_PATH = mod.DB_FILE_PATH
# Non frame widget padx
PADX = 5
# Non-frame widgets to right of first widget
RPADX = (20, PADX)

# Frame padding
FRM_PADX = 10
# Frames to right of left-most frame
FRM_RPADX = (0, FRM_PADX)
FRM_PADY = 5
# Very top frame pady
FRM_TPADY = (FRM_PADY * 2, FRM_PADY)
# Very bottom frame pady
FRM_BPADY = (FRM_PADY, FRM_PADY * 2)


class PreferencesDialog(ctk.CTkToplevel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.columnconfigure(0, weight=1)

        this_platform = platform.system()
        if this_platform == "Darwin":
            self.platform = "MacOS"

        icon_photo = tk.PhotoImage(file=APP_IMAGES / 'bear-logo-colour-dark.png')
        self.iconphoto(False, icon_photo)
        control_panel_theme = pref.preference_setting(db_file_path=DB_FILE_PATH,
                                                      scope='user_preference', preference_name='control_panel_theme')

        control_panel_theme = control_panel_theme + '.json'

        self.control_panel_theme = str(APP_THEMES_DIR / control_panel_theme)

        self.control_panel_mode = pref.preference_setting(db_file_path=DB_FILE_PATH,
                                                          scope='user_preference', preference_name='control_panel_mode')

        self.last_theme_on_start = pref.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                           preference_name='last_theme_on_start')

        self.theme_author = pref.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                    preference_name='theme_author')

        self.enable_tooltips = pref.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                       preference_name='enable_tooltips')

        self.confirm_cascade = pref.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                       preference_name='confirm_cascade')

        self.enable_palette_labels = pref.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                             preference_name='enable_palette_labels')

        self.enable_single_click_paste = pref.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                                 preference_name='enable_single_click_paste')

        self.shade_adjust_differential = pref.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                                 preference_name='shade_adjust_differential')

        self.harmony_contrast_differential = pref.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                                     preference_name='harmony_contrast_differential')

        self.theme_json_dir = pref.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                      preference_name='theme_json_dir')

        self.control_panel_scaling = pref.preference_setting(db_file_path=DB_FILE_PATH,
                                                             scope='scaling',
                                                             preference_name='control_panel')

        self.preview_panel_scaling = pref.preference_setting(db_file_path=DB_FILE_PATH,
                                                             scope='scaling',
                                                             preference_name='preview_panel')

        self.listener_port = pref.preference_setting(db_file_path=DB_FILE_PATH,
                                                     scope='user_preference',
                                                     preference_name='listener_port')

        self.qa_application_scaling = pref.preference_setting(db_file_path=DB_FILE_PATH,
                                                              scope='scaling',
                                                              preference_name='qa_application')

        log_level = pref.preference_setting(scope='logger', preference_name='log_level', default="Info")

        self.log_level = log_level.upper()
        self.log_stderr = pref.preference_setting(scope='logger', preference_name='log_stderr', default="Yes")

        self.action = 'cancelled'

        self.new_theme_json_dir = self.theme_json_dir
        # Establish the user login name and home directory        this_platform = platform.system()
        if this_platform == "Windows":
            self.user_home_dir = os.getenv("UserProfile")
            self.user_name = os.getenv("LOGNAME")
        else:
            self.user_name = os.getenv("USER")
            self.user_home_dir = os.getenv("HOME")

        self.title('CTk Theme Builder Preferences')

        frm_main = ctk.CTkFrame(master=self, corner_radius=10)
        frm_main.grid(column=0, row=0, sticky='nsew')
        frm_main.columnconfigure(0, weight=1)
        frm_main.rowconfigure(0, weight=1)

        # Provenance frame
        frm_provenance = ctk.CTkFrame(master=frm_main, corner_radius=10)
        frm_provenance.grid(column=0, row=0,
                            padx=FRM_PADX, pady=FRM_TPADY,
                            columnspan=2, sticky='nsew')
        lbl_provenance = ctk.CTkLabel(master=frm_provenance, text='Provenance', justify="right", font=mod.HEADING4)
        lbl_provenance.grid(row=0, column=0, padx=5, pady=(5, 5), sticky='e')

        lbl_author_name = ctk.CTkLabel(master=frm_provenance, text='Author', justify="right")
        lbl_author_name.grid(row=1, column=0, padx=5, pady=(5, 5), sticky='e')

        if not self.theme_author:
            self.theme_author = self.user_name
        self.tk_author_name = tk.StringVar(value=self.theme_author)
        self.ent_author_name = ctk.CTkEntry(master=frm_provenance,
                                            textvariable=self.tk_author_name,
                                            width=160)
        self.ent_author_name.grid(row=1, column=1, padx=(0, 0), pady=(5, 5), sticky='w')

        if self.enable_tooltips:
            CTkToolTip(lbl_author_name,
                       wraplength=250,
                       justify="left",
                       border_width=1,
                       padding=(10, 10),
                       corner_radius=6,
                       message="The author's name is included to the theme JSON, in the "
                               "provenance section.")

        # Appearance frame
        frm_appearance = ctk.CTkFrame(master=frm_main, corner_radius=10)
        frm_appearance.grid(column=0, row=1,
                            padx=FRM_PADX, pady=FRM_PADY,
                            columnspan=1, sticky='nsew')
        lbl_appearance = ctk.CTkLabel(master=frm_appearance,
                                      text='Appearance',
                                      justify="right", font=mod.HEADING4)
        lbl_appearance.grid(row=0, column=0, padx=5, pady=(5, 5), sticky='w')

        lbl_theme = ctk.CTkLabel(master=frm_appearance, text='Panel Theme', justify="right")
        lbl_theme.grid(row=1, column=0, padx=5, pady=5, sticky='e')

        if self.enable_tooltips:
            btn_author_tooltip = CTkToolTip(lbl_theme,
                                            wraplength=250,
                                            justify="left",
                                            border_width=1,
                                            padding=(10, 10),
                                            corner_radius=6,
                                            message="The default theme for the CTk Theme Builder main application, "
                                                    "is GreyGhost, however you can override this here. "
                                                    "\n\n"
                                                    "TIP: For a darker theme, Oceanix may be a better choice.")

        control_panel_theme = os.path.splitext(self.control_panel_theme)[0]
        control_panel_theme = os.path.basename(control_panel_theme)
        self.tk_control_panel_theme = tk.StringVar(value=control_panel_theme)
        self.opm_control_panel_theme = ctk.CTkOptionMenu(master=frm_appearance,
                                                         variable=self.tk_control_panel_theme,
                                                         values=mod.app_themes_list())
        self.opm_control_panel_theme.grid(row=1, column=1, padx=0, pady=5, sticky='w')

        lbl_mode = ctk.CTkLabel(master=frm_appearance, text='Appearance Mode', justify="right")
        lbl_mode.grid(row=1, column=2, padx=RPADX, sticky='w')

        # The control_panel_mode holds the  CustomTkinter appearance mode (Dark / Light)
        self.tk_appearance_mode_var = tk.StringVar(value=self.control_panel_mode)
        rdo_light = ctk.CTkRadioButton(master=frm_appearance, text='Light', variable=self.tk_appearance_mode_var,
                                       value='Light')
        rdo_light.grid(row=1, column=3, sticky='w')

        rdo_dark = ctk.CTkRadioButton(master=frm_appearance, text='Dark', variable=self.tk_appearance_mode_var,
                                      value='Dark')
        rdo_dark.grid(row=2, column=3, pady=5, sticky='w')

        if self.control_panel_mode == 'Dark':
            rdo_light.deselect()
            rdo_dark.select()
        elif self.control_panel_mode == 'Light':
            rdo_dark.deselect()
            rdo_light.select()

        lbl_control_panel_scaling = ctk.CTkLabel(master=frm_appearance, text='Control Panel Scaling', justify="left")
        lbl_control_panel_scaling.grid(row=3, column=0, padx=(10, 5), pady=10, sticky='e')

        self.opm_control_panel_scaling = ctk.CTkOptionMenu(master=frm_appearance,
                                                           width=12,
                                                           values=mod.ui_scaling_list())
        self.opm_control_panel_scaling.grid(row=3, column=1, padx=0, pady=10, sticky='w')
        self.opm_control_panel_scaling.set(self.control_panel_scaling)

        lbl_preview_panel_scaling = ctk.CTkLabel(master=frm_appearance, text='Preview Panel Scaling', justify="left")
        lbl_preview_panel_scaling.grid(row=3, column=2, padx=(0, 5), pady=10, sticky='e')

        self.opm_preview_panel_scaling = ctk.CTkOptionMenu(master=frm_appearance,
                                                           width=12,
                                                           values=mod.ui_scaling_list())
        self.opm_preview_panel_scaling.grid(row=3, column=3, padx=0, pady=10, sticky='w')
        self.opm_preview_panel_scaling.set(self.preview_panel_scaling)

        lbl_qa_application_scaling = ctk.CTkLabel(master=frm_appearance, text='QA App Scaling', justify="right")
        lbl_qa_application_scaling.grid(row=4, column=0, padx=(5, 5), pady=10, sticky='e')

        self.opm_qa_application_scaling = ctk.CTkOptionMenu(master=frm_appearance,
                                                            width=12,
                                                            values=mod.ui_scaling_list())
        self.opm_qa_application_scaling.grid(row=4, column=1, padx=0, pady=10, sticky='w')
        self.opm_qa_application_scaling.set(self.qa_application_scaling)

        # Colour controls frame
        frm_colour = ctk.CTkFrame(master=frm_main, corner_radius=10)
        frm_colour.grid(column=1, row=1,
                        padx=FRM_RPADX, pady=FRM_PADY,
                        sticky='nsew')
        lbl_colour = ctk.CTkLabel(master=frm_colour, text='Colour Controls', justify="right", font=mod.HEADING4)
        lbl_colour.grid(row=0, column=0, padx=PADX, pady=(5, 5), sticky='w')

        lbl_shade_adjust_differential = ctk.CTkLabel(master=frm_colour, text='Adjust Shade Step', justify="right")
        lbl_shade_adjust_differential.grid(row=1, column=0, padx=5, pady=10, sticky='e')

        self.opm_shade_adjust_differential = ctk.CTkOptionMenu(master=frm_colour,
                                                               width=12,
                                                               values=['1', '2', '3', '4', '5', '6', '7', '8', '9'])
        self.opm_shade_adjust_differential.grid(row=1, column=1, padx=(5, 100), pady=10, sticky='w')
        self.opm_shade_adjust_differential.set(str(self.shade_adjust_differential))

        lbl_harmony_contrast_differential = ctk.CTkLabel(master=frm_colour, text='Harmony Shade Step', justify="right")
        lbl_harmony_contrast_differential.grid(row=2, column=0, padx=(10, 5), pady=(0, 0), sticky='e')

        self.opm_harmony_contrast_differential = ctk.CTkOptionMenu(master=frm_colour,
                                                                   width=12,
                                                                   values=['1', '2', '3', '5', '6', '7', '8', '9'])
        self.opm_harmony_contrast_differential.grid(row=2, column=1, padx=(5, 100), pady=5, sticky='w')
        self.opm_harmony_contrast_differential.set(str(self.harmony_contrast_differential))

        # Behaviour frame
        frm_behaviour = ctk.CTkFrame(master=frm_main, corner_radius=10)
        frm_behaviour.grid(column=0, row=2,
                           padx=FRM_PADX, pady=FRM_PADY,
                           sticky='nsew')
        lbl_behaviour = ctk.CTkLabel(master=frm_behaviour, text='Behaviour', justify="right", font=mod.HEADING4)
        lbl_behaviour.grid(row=0, column=0, padx=PADX, pady=(5, 5), sticky='w')

        self.tk_enable_tooltips = tk.IntVar(master=frm_behaviour)
        self.tk_enable_tooltips.set(self.enable_tooltips)
        self.swt_enable_tooltips = ctk.CTkSwitch(master=frm_behaviour,
                                                 text='Tooltips',
                                                 variable=self.tk_enable_tooltips,
                                                 command=self.get_tooltips_setting)
        self.swt_enable_tooltips.grid(row=1, column=0, padx=PADX, pady=10, sticky='w')

        CTkToolTip(self.swt_enable_tooltips,
                   wraplength=250,
                   justify="left",
                   border_width=1,
                   padding=(10, 10),
                   corner_radius=6,
                   message="When enabled, this causes tool-tips to be enabled "
                           "throughout the theme builder application."
                           "\n\n"
                           "Any changes will not take effect until after you "
                           "re-start the application.")

        self.tk_confirm_cascade = tk.IntVar(master=frm_behaviour)
        self.tk_confirm_cascade.set(self.confirm_cascade)
        self.swt_confirm_cascade = ctk.CTkSwitch(master=frm_behaviour,
                                                 text='Confirm cascade',
                                                 variable=self.tk_confirm_cascade,
                                                 command=self.get_cascade_setting)
        self.swt_confirm_cascade.grid(row=1, column=1, padx=RPADX, pady=10, sticky='w')

        if self.enable_tooltips:
            CTkToolTip(self.swt_confirm_cascade,
                       wraplength=250,
                       justify="left",
                       border_width=1,
                       padding=(10, 10),
                       corner_radius=6,
                       message="When enabled, causes causes a pop-up, confirmation dialog"
                               " to appear, whenever a colour cascade is invoked from the "
                               "floating menu, on the theme's colour palette.")

        self.tk_enable_palette_labels = tk.IntVar(master=frm_behaviour)
        self.tk_enable_palette_labels.set(self.enable_palette_labels)
        self.swt_enable_palette_labels = ctk.CTkSwitch(master=frm_behaviour,
                                                       text='Theme Palette Labels',
                                                       variable=self.tk_enable_palette_labels,
                                                       command=self.get_palette_label_setting)
        self.swt_enable_palette_labels.grid(row=1, column=2, padx=RPADX, pady=10, sticky='w')

        if self.enable_tooltips:
            CTkToolTip(self.swt_enable_palette_labels,
                       border_width=1,
                       justify="left",
                       padding=(10, 10),
                       corner_radius=6,
                       message="Enable/disable the rendering of the colour palette "
                               "labels.")

        self.tk_last_theme_on_start = tk.IntVar(master=frm_behaviour, value=self.last_theme_on_start)
        self.tk_last_theme_on_start.set(self.last_theme_on_start)
        self.swt_last_theme_on_start = ctk.CTkSwitch(master=frm_behaviour,
                                                     text='Load Last Theme',
                                                     variable=self.tk_last_theme_on_start,
                                                     command=self.get_last_theme_on_start)
        self.swt_last_theme_on_start.grid(row=2, column=0, padx=PADX, pady=10, sticky='w')
        if self.enable_tooltips:
            CTkToolTip(self.swt_last_theme_on_start,
                       wraplength=250,
                       justify="left",
                       border_width=1,
                       padding=(10, 10),
                       corner_radius=6,
                       message="Enable this switch, to auto-select and open, at application startup, the last theme "
                               "you worked on.")

        self.tk_enable_single_click_paste = tk.IntVar(master=frm_behaviour)
        self.tk_enable_single_click_paste.set(self.enable_single_click_paste)
        self.swt_enable_single_click_paste = ctk.CTkSwitch(master=frm_behaviour,
                                                           text='Single Click Paste',
                                                           variable=self.tk_enable_single_click_paste,
                                                           command=self.get_single_click_paste_setting)
        self.swt_enable_single_click_paste.grid(row=2, column=1, padx=RPADX, pady=10, sticky='w')

        if self.enable_tooltips:
            CTkToolTip(self.swt_enable_single_click_paste,
                       wraplength=400,
                       border_width=1,
                       justify="left",
                       padding=(10, 10),
                       corner_radius=6,
                       message="Enable/disable colour pasting, via a single click. "
                               "Colours can be pasted to the colour palette or the array "
                               "of widget colour properties.")

        # Comms frame
        frm_comms = ctk.CTkFrame(master=frm_main, corner_radius=10)
        frm_comms.grid(column=1, row=2,
                       padx=FRM_RPADX, pady=FRM_PADY,
                       sticky='nsew')
        lbl_comms = ctk.CTkLabel(master=frm_comms, text='Comms', justify="right", font=mod.HEADING4)
        lbl_comms.grid(row=0, column=0, padx=5, pady=(5, 5), sticky='w')

        lbl_listener_port = ctk.CTkLabel(master=frm_comms, text='Listener Port', justify="right")
        lbl_listener_port.grid(row=1, column=0, padx=5, pady=10, sticky='w')

        self.opm_listener_port = ctk.CTkOptionMenu(master=frm_comms,
                                                   width=12,
                                                   values=['5051', '5052', '5053', '5054', '5055'])
        self.opm_listener_port.grid(row=1, column=1, padx=(5, 100), pady=10, sticky='w')
        self.opm_listener_port.set(str(self.listener_port))

        if self.enable_tooltips:
            lbl_listener_port_tooltip = CTkToolTip(lbl_listener_port,
                                                   wraplength=400,
                                                   justify='left',
                                                   border_width=1,
                                                   padding=(10, 10),
                                                   corner_radius=6,
                                                   message="Here you can change the listener port for the Preview "
                                                           "Panel.\n\nYou can modify this, if for example, you want to "
                                                           "run multiple instances of the application. Each instance "
                                                           "with its own port number.")

        # Themes frame
        frm_themes = ctk.CTkFrame(master=frm_main, corner_radius=10)
        frm_themes.grid(column=0, row=3,
                        padx=FRM_PADX, pady=FRM_BPADY,
                        sticky='nsew')
        lbl_behaviour = ctk.CTkLabel(master=frm_themes, text='User Themes', justify="right", font=mod.HEADING4)
        lbl_behaviour.grid(row=0, column=0, padx=5, pady=(5, 5), sticky='w')

        self.folder_image = cbtk.load_image(light_image=APP_IMAGES / 'folder.png', image_size=(20, 20))
        lbl_theme_json_dir = ctk.CTkLabel(master=frm_themes, text='Themes Location', justify="right")
        lbl_theme_json_dir.grid(row=1, column=0, padx=5, pady=(15, 5), sticky='e')

        if self.enable_tooltips:
            lbl_theme_json_dir_tooltip = CTkToolTip(lbl_theme_json_dir,
                                                    border_width=1,
                                                    justify="left",
                                                    padding=(10, 10),
                                                    corner_radius=6,
                                                    message="Select a location to store your themes.")

        btn_theme_json_dir = ctk.CTkButton(master=frm_themes,
                                           text='',
                                           width=30,
                                           height=30,
                                           fg_color='#748696',
                                           image=self.folder_image,
                                           command=self.preferred_json_location)
        btn_theme_json_dir.grid(row=1, column=1, pady=(10, 0), sticky='w')

        self.lbl_pref_theme_dir_disp = ctk.CTkLabel(master=frm_themes, text=self.theme_json_dir, justify="left",
                                                    font=mod.REGULAR_TEXT)
        self.lbl_pref_theme_dir_disp.grid(row=2, column=1, columnspan=5, padx=5, pady=5, sticky='w')

        # Logging frame
        frm_logging = ctk.CTkFrame(master=frm_main, corner_radius=10)
        frm_logging.grid(column=1, row=3,
                         padx=FRM_RPADX, pady=FRM_BPADY,
                         sticky='nsew')
        lbl_logging = ctk.CTkLabel(master=frm_logging, text='Logging', justify="right", font=mod.HEADING4)
        lbl_logging.grid(row=0, column=0, padx=5, pady=(5, 5), sticky='w')

        lbl_log_level = ctk.CTkLabel(master=frm_logging, text='Logging Level', justify="right")
        lbl_log_level.grid(row=1, column=0, padx=PADX, pady=10, sticky='e')

        if self.enable_tooltips:
            CTkToolTip(lbl_log_level,
                       wraplength=400,
                       justify="left",
                       border_width=1,
                       padding=(10, 10),
                       corner_radius=6,
                       message="Allows you to adjust logging level. More details are logged, "
                               "with selections made closer to the top of the list. "
                               "Typically you should have this set to Info or Warning."
                               "\n\n"
                               "Any changes will not take effect until after you "
                               "re-start the application.")

        self.opm_log_level = ctk.CTkOptionMenu(master=frm_logging,
                                               width=12,
                                               values=log.LOG_LEVEL_DISP)

        self.opm_log_level.grid(row=1, column=1, padx=PADX, pady=10, sticky='w')
        self.opm_log_level.set(str(self.log_level.title()))

        lbl_log_stderr = ctk.CTkLabel(master=frm_logging, text='Log to stderr', justify="right")
        lbl_log_stderr.grid(row=2, column=0, padx=5, pady=10, sticky='e')

        if self.enable_tooltips:
            CTkToolTip(lbl_log_stderr,
                       border_width=1,
                       justify="left",
                       padding=(10, 10),
                       corner_radius=6,
                       message=f"Typically, we only log to the {logutl.RUNTIME_LOG} file, in the log "
                               'folder.\n\nSelect "Yes", to duplex logging to the terminal.')

        self.opm_log_stderr = ctk.CTkOptionMenu(master=frm_logging,
                                                width=12,
                                                values=['Yes', 'No'])
        self.opm_log_stderr.grid(row=2, column=1, padx=PADX, pady=10, sticky='w')
        self.opm_log_stderr.set(str(self.log_stderr))

        lbl_log_size_label = ctk.CTkLabel(master=frm_logging, text='Log size (bytes):', justify="right")
        lbl_log_size_label.grid(row=3, column=0, padx=PADX, pady=10, sticky='e')

        log_size = logutl.logfile_size()
        formatted_log_size = format(log_size, ",")
        self.lbl_log_size = ctk.CTkLabel(master=frm_logging, text=formatted_log_size, justify="right")
        self.lbl_log_size.grid(row=3, column=1, padx=PADX, pady=10, sticky='w')

        btn_clear_log = ctk.CTkButton(master=frm_logging, text='Clear Log', command=self.clear_log, width=15)
        btn_clear_log.grid(row=3, column=3, padx=(15, 0), pady=5)

        CTkToolTip(btn_clear_log,
                   border_width=1,
                   justify="left",
                   padding=(10, 10),
                   corner_radius=6,
                   message=f"Clear down the runtime log, which is located at:\n {logutl.LOG_DIR / logutl.RUNTIME_LOG}")

        # Dialog buttons frame
        frm_buttons = ctk.CTkFrame(master=frm_main, corner_radius=0)
        frm_buttons.grid(column=0, row=10, padx=0, pady=(0, 0), columnspan=2, sticky='ew')

        # Dialog buttons
        btn_close = ctk.CTkButton(master=frm_buttons, text='Cancel', command=self.close_preferences)
        btn_close.grid(row=0, column=0, padx=(15, 35), pady=5)

        btn_save = ctk.CTkButton(master=frm_buttons, text='Save', command=self.save_preferences)
        btn_save.grid(row=0, column=1, padx=(520, 15), pady=5)

        self.status_bar = cbtk.CBtkStatusBar(master=self,
                                             status_text_life=30,
                                             use_grid=True)

        self.bind("<Configure>", self.status_bar.auto_size_status_bar)

        self.grab_set()
        self.lift()
        self.resizable(False, False)
        self.bind('<Escape>', self.close_preferences)

    def clear_log(self, event=None):
        confirm = CTkMessagebox(master=self,
                                title='Confirm Action',
                                message=f'Are you sure you wish to erase the runtime log contents?',
                                options=["Yes", "No"])
        response = confirm.get()
        if response == 'No':
            return

        logutl.truncate_log()
        log_size = logutl.logfile_size()
        formatted_log_size = format(log_size, ",")
        self.lbl_log_size.configure(text=formatted_log_size)

        self.status_bar.set_status_text('Runtime log contents cleared.')
        log.log_warning(log_text=f'Runtime log contents cleared.',
                     class_name='PreferencesDialog',
                     method_name='clear_log')

    @log_call
    def close_preferences(self, event=None):
        log.log_debug(log_text='Closing preferences dialogue',
                      class_name='PreferencesDialog',
                      method_name='close_preferences')
        self.destroy()

    @log_call
    def get_cascade_setting(self):
        self.confirm_cascade = int(self.tk_confirm_cascade.get())

    @log_call
    def get_tooltips_setting(self):
        self.enable_tooltips = int(self.tk_enable_tooltips.get())

    @log_call
    def get_palette_label_setting(self):
        self.enable_palette_labels = int(self.tk_enable_palette_labels.get())

    @log_call
    def get_last_theme_on_start(self):
        self.last_theme_on_start = int(self.tk_last_theme_on_start.get())

    @log_call
    def get_single_click_paste_setting(self):
        self.enable_single_click_paste = int(self.tk_enable_single_click_paste.get())

    @log_call
    def save_preferences(self):
        """Save the selected preferences."""
        # Save JSON Directory:
        # If the directory selection was cancelled, we end up with
        # the string representation of the path, returning as a dot.
        log.log_debug(log_text='Save preferences and close dialogue',
                      class_name='PreferencesDialog',
                      method_name='save_preferences')
        if str(self.new_theme_json_dir) != '.':
            self.theme_json_dir = self.new_theme_json_dir
            if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='user_preference',
                                               preference_name='theme_json_dir',
                                               preference_value=str(self.theme_json_dir)):
                print(f'Row miss updating preferences: user_preference > theme_json_dir')
            self.json_files = mod.user_themes_list()
            # TODO: Implement signal to improve this
            self.master.opm_theme.configure(values=self.json_files)

        self.user_name = self.tk_author_name.get()

        if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='user_preference',
                                           preference_name='theme_author', preference_value=self.user_name):
            log.log_error(log_text=f'Row miss updating preferences: user_preference > theme_author')

        if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='user_preference',
                                           preference_name='control_panel_theme',
                                           preference_value=self.opm_control_panel_theme.get()):
            log.log_error(log_text=f'Row miss updating preferences: user_preference > control_panel_theme')

        control_panel_mode = self.tk_appearance_mode_var.get()
        if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='user_preference',
                                           preference_name='control_panel_mode',
                                           preference_value=control_panel_mode):
            log.log_error(log_text=f'Row miss updating preferences: user_preference > control_panel_mode')

        if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='user_preference',
                                           preference_name='enable_tooltips',
                                           preference_value=self.enable_tooltips):
            log.log_error(log_text=f'Row miss updating preferences: user_preference > enable_tooltips')

        if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='user_preference',
                                           preference_name='confirm_cascade',
                                           preference_value=self.confirm_cascade):
            log.log_error(log_text=f'Row miss updating preferences: user_preference > confirm_cascade')

        if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='user_preference',
                                           preference_name='last_theme_on_start',
                                           preference_value=self.last_theme_on_start):
            log.log_error(log_text=f'Row miss updating preferences: user_preference > last_theme_on_start')

        if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='user_preference',
                                           preference_name='enable_palette_labels',
                                           preference_value=self.enable_palette_labels):
            log.log_error(log_text=f'Row miss updating preferences: user_preference > enable_palette_labels')

        if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='user_preference',
                                           preference_name='enable_single_click_paste',
                                           preference_value=self.enable_single_click_paste):
            log.log_error(log_text=f'Row miss updating preferences: user_preference > enable_single_click_paste')

        self.shade_adjust_differential = self.opm_shade_adjust_differential.get()
        self.shade_adjust_differential = int(self.shade_adjust_differential)
        if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='user_preference',
                                           preference_name='shade_adjust_differential',
                                           preference_value=self.shade_adjust_differential):
            log.log_error(log_text=f'Row miss updating preferences: user_preference > shade_adjust_differential')

        self.harmony_contrast_differential = self.opm_harmony_contrast_differential.get()
        self.harmony_contrast_differential = int(self.harmony_contrast_differential)
        if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='user_preference',
                                           preference_name='harmony_contrast_differential',
                                           preference_value=self.harmony_contrast_differential):
            log.log_error(log_text=f'Row miss updating preferences: user_preference > harmony_contrast_differential')

        control_panel_scaling_pct = self.opm_control_panel_scaling.get()
        if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='scaling',
                                           preference_name='control_panel',
                                           preference_value=control_panel_scaling_pct):
            log.log_error(log_text=f'Row miss updating preferences: scaling > control_panel')
        if control_panel_scaling_pct != self.master.control_panel_scaling_pct:
            scaling_float = mod.scaling_float(scale_pct=control_panel_scaling_pct)
            ctk.set_widget_scaling(scaling_float)
            self.master.control_panel_scaling_pct = control_panel_scaling_pct
            # TODO: Implement signal to improve this
            self.master.geometry('960x870')

        preview_panel_scale_pct = self.opm_preview_panel_scaling.get()
        if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='scaling',
                                           preference_name='preview_panel',
                                           preference_value=preview_panel_scale_pct):
            log.log_error(log_text=f'Row miss updating preferences: scaling > preview_panel')

        if preview_panel_scale_pct != self.master.preview_panel_scaling_pct and self.master.theme:
            self.master.preview_panel_scaling_pct = preview_panel_scale_pct
            mod.send_command_json(command_type='program',
                                  command='set_widget_scaling',
                                  parameters=[preview_panel_scale_pct])

        qa_application_scale_pct = self.opm_qa_application_scaling.get()
        if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='scaling',
                                           preference_name='qa_application',
                                           preference_value=qa_application_scale_pct):
            log.log_error(log_text=f'Row miss updating preferences: scaling > qa_application')

        listener_port = self.opm_listener_port.get()
        if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='user_preference',
                                           preference_name='listener_port',
                                           preference_value=listener_port):
            log.log_error(log_text=f'Row miss updating preferences: user_preference > listener port')

        log_level = self.opm_log_level.get()
        if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='logger',
                                           preference_name='log_level',
                                           preference_value=log_level.upper()):
            log.log_error(log_text=f'Row miss updating logger > log_level')

        log_stderr = self.opm_log_stderr.get()
        if not mod.update_preference_value(db_file_path=DB_FILE_PATH, scope='logger',
                                           preference_name='log_stderr',
                                           preference_value=log_stderr):
            log.log_error(log_text=f'Row miss updating logger > log_stderr')

        ctk.set_appearance_mode(control_panel_mode)
        cbtk.CBtkMenu.update_widgets_mode()
        self.control_panel_mode = control_panel_mode
        self.tk_appearance_mode_var.set(self.control_panel_mode)
        self.action = 'saved'
        self.destroy()

    @log_call
    def preferred_json_location(self):
        """A simple method which asks the themes author to navigate to where
         the themes JSON are to be stored/maintained."""
        self.new_theme_json_dir = Path(ctk.filedialog.askdirectory(initialdir=self.theme_json_dir))
        if str(self.new_theme_json_dir) != '.':
            self.lbl_pref_theme_dir_disp.configure(text=self.new_theme_json_dir)
