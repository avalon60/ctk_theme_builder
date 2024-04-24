"""Class container for the colour Harmonics Dialog class."""

from CTkToolTip import CTkToolTip
import model.ctk_theme_builder as mod
from model.ctk_theme_builder import log_call
import customtkinter as ctk
import tkinter as tk
import pyperclip

import utils.cbtk_kit as cbtk
import model.preferences as pref
import utils.loggerutl as log

import colorharmonies as ch
from tkinter.colorchooser import askcolor

APP_THEMES_DIR = mod.APP_THEMES_DIR
APP_IMAGES = mod.APP_IMAGES
DB_FILE_PATH = mod.DB_FILE_PATH
TEMP_DIR = mod.TEMP_DIR

HEADING1 = mod.HEADING1
HEADING2 = mod.HEADING2
HEADING3 = mod.HEADING3
HEADING4 = mod.HEADING4

REGULAR_TEXT = cbtk.REGULAR_TEXT
SMALL_TEXT = mod.SMALL_TEXT


class HarmonicsDialog(ctk.CTkToplevel):

    def __init__(self, theme_name, theme_json_data: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        icon_photo = tk.PhotoImage(file=APP_IMAGES / 'bear-logo-colour-dark.png')
        self.iconphoto(False, icon_photo)
        self.HARMONICS_HEIGHT1 = 550
        self.HARMONICS_HEIGHT2 = 550
        self.HARMONICS_HEIGHT3 = 650
        self.theme_json_data = theme_json_data
        self.rendered_harmony_buttons = []
        self.rendered_keystone_shades = []
        self.theme_name = theme_name

        self.harmony_contrast_differential = pref.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                                     preference_name='harmony_contrast_differential')

        self.enable_tooltips = pref.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                       preference_name='enable_tooltips')

        control_panel_theme = pref.preference_setting(db_file_path=DB_FILE_PATH,
                                                      scope='user_preference', preference_name='control_panel_theme')

        control_panel_theme = control_panel_theme + '.json'

        self.control_panel_theme = str(APP_THEMES_DIR / control_panel_theme)
        # The control_panel_mode holds the  CustomTkinter appearance mode (Dark / Light)

        self.control_panel_mode = pref.preference_setting(db_file_path=DB_FILE_PATH,
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

        self.title('Colour Harmonics')

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.restore_harmony_geometry()

        frm_main = ctk.CTkFrame(master=self, corner_radius=0)
        frm_main.grid(column=0, row=0, sticky='nsew')
        frm_main.columnconfigure(0, weight=1)
        frm_main.rowconfigure(0, weight=1)

        frm_controls = ctk.CTkFrame(master=frm_main)
        frm_controls.grid(column=0, row=0, padx=10, pady=10, sticky='new')

        self.frm_harmony_colours = ctk.CTkFrame(master=frm_main)
        self.frm_harmony_colours.grid(column=0, row=1, padx=10, pady=10, sticky='nsew')

        self.frm_shades_palette = ctk.CTkFrame(master=frm_main)
        self.frm_shades_palette.grid(column=2, row=0, padx=(0, 10), pady=10, sticky='nsew', rowspan=2)

        frm_buttons = ctk.CTkFrame(master=frm_main, border_width=0)
        frm_buttons.grid(column=0, row=2, padx=10, pady=(0, 5), sticky='ew', columnspan=3)

        self.harmony_status_bar = cbtk.CBtkStatusBar(master=self,
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

        if self.theme_name is not None:
            button_state = ctk.NORMAL
        else:
            button_state = ctk.DISABLED

        btn_close = ctk.CTkButton(master=frm_buttons,
                                  text='Close',
                                  command=self.close_harmonics)

        btn_close.grid(row=0, column=0, padx=15, pady=5)

        btn_copy_to_palette = ctk.CTkButton(master=frm_buttons,
                                            text='Copy to Palette',
                                            state=button_state,
                                            command=self.copy_harmonics_to_palette)

        if self.enable_tooltips:
            btn_tooltip = CTkToolTip(btn_copy_to_palette,
                                     wraplength=250,
                                     justify="left",
                                     border_width=1,
                                     padding=(10, 10),
                                     corner_radius=6,
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
                                         border_width=1,
                                         padding=(10, 10),
                                         corner_radius=6,
                                         message='Tag this keystone colour to the theme.\n\nThis will cause the '
                                                 'keystone colour to be restored when the theme is opened and the '
                                                 'Colour Harmonics dialog opened.')

        harmony_method = self.theme_json_data.get('provenance', {}).get('harmony method', None)
        self.set_harmony_keystone(colour_code=bg_colour, method=harmony_method)
        self.switch_harmony_method()
        self.harmony_palette_running = True
        # self.master.set_option_states()
        self.protocol("WM_DELETE_WINDOW", self.close_harmonics)
        self.bind('<Escape>', self.close_harmonics)
        self.grab_set()
        self.lift()

    @staticmethod
    @log_call
    def context_menu(event: tk.Event = None, menu: cbtk.CBtkMenu = None):
        menu.tk_popup(event.x_root, event.y_root)

    @log_call
    def restore_harmony_geometry(self):
        """Restore window geometry from auto-saved preferences"""
        saved_geometry = pref.preference_setting(db_file_path=DB_FILE_PATH,
                                                 scope='window_geometry',
                                                 preference_name='harmonics_panel')
        self.geometry(saved_geometry)
        self.resizable(False, False)

    @log_call
    def copy_harmony_input_colour(self, event=None):
        colour = self.btn_keystone_colour.cget('fg_color')
        log.log_debug(log_text=f'Copy harmony input colour, {colour} to clipboard', class_name='HarmonicsDialog',
                      method_name='copy_harmony_input_colour')
        pyperclip.copy(colour)
        self.harmony_status_bar.set_status_text(
            status_text=f'Colour {colour} copied to clipboard.')

    @log_call
    def paste_harmony_keystone_colour(self):
        """Paste the colour currently stored in the paste buffer, to the harmony input button."""
        new_colour = pyperclip.paste()
        log.log_debug(log_text=f'Paste harmony input colour, {new_colour} from clipboard',
                      class_name='HarmonicsDialog',
                      method_name='paste_harmony_keystone_colour')
        if not cbtk.valid_colour(new_colour):
            self.harmony_status_bar.set_status_text(status_text='Attempted paste of non colour code text - ignored.')
            return
        harmony_method = self.opm_harmony_method.get()
        self.set_harmony_keystone(colour_code=new_colour, method=harmony_method)
        self.populate_harmony_colours()
        self.harmony_status_bar.set_status_text(
            status_text=f'Colour {new_colour} assigned.')

    @log_call
    def set_harmony_keystone(self, colour_code: str, method: str):
        hover_colour = cbtk.contrast_colour(colour_code)
        if colour_code:
            self.btn_keystone_colour.configure(fg_color=colour_code,
                                               hover_color=hover_colour)

        if method:
            # set the harmony method, as tagged in the theme file.
            self.opm_harmony_method.set(method)
            self.keystone_colour = colour_code
            log.log_debug(log_text=f'Set harmony keystone colour: {colour_code}',
                          class_name='HarmonicsDialog',
                          method_name='set_harmony_keystone')

    @log_call
    def copy_keystone_colour(self, event=None, harmony_button_id=None, shade_copy=False):
        colour = self.rendered_keystone_shades[harmony_button_id].cget('fg_color')
        if shade_copy:
            colour = cbtk.contrast_colour(colour, self.shade_adjust_differential)
        log.log_debug(log_text=f'Copy keystone colour: {colour}',
                      class_name='HarmonicsDialog',
                      method_name='copy_keystone_colour')
        pyperclip.copy(colour)
        self.harmony_status_bar.set_status_text(
            status_text=f'Colour {colour} copied from palette entry {harmony_button_id + 1} to clipboard.')

    @log_call
    def copy_harmony_colour(self, event=None, harmony_button_id=None, shade_copy=False):
        colour = self.rendered_harmony_buttons[harmony_button_id].cget('fg_color')
        log.log_debug(log_text=f'Copy harmony colour: {colour}',
                      class_name='HarmonicsDialog',
                      method_name='copy_harmony_colour')
        pyperclip.copy(colour)

        self.harmony_status_bar.set_status_text(
            status_text=f'Colour {colour} copied from palette entry {harmony_button_id + 1} to clipboard.')

    @log_call
    def harmony_input_colour_picker(self):

        log.log_debug(log_text='Launch harmony colour picker',
                      class_name='HarmonicsDialog',
                      method_name='harmony_input_colour_picker')

        # self.harmonics_label_count
        self.lift()
        self.transient()
        primary_colour = askcolor(master=self,
                                  initialcolor=self.keystone_colour,
                                  title=f'Harmony Source Colour Selection')

        if primary_colour[1] is not None:
            primary_colour = primary_colour[1]
            self.btn_keystone_colour.configure(fg_color=primary_colour,
                                               hover_color=primary_colour)
            self.harmony_status_bar.set_status_text(
                status_text=f'Colour {primary_colour} assigned.')
            self.keystone_colour = primary_colour
            self.populate_harmony_colours()

    @log_call
    def harmony_colour_picker(self, palette_button_id):
        # self.harmonics_label_count
        primary_colour = askcolor(master=self,
                                  title=f'Harmony Source Colour Selection')

        if primary_colour[1] is not None:
            primary_colour = primary_colour[1]
            self.rendered_harmony_buttons[0].configure(fg_color=primary_colour,
                                                       hover_color=primary_colour)
            self.harmony_status_bar.set_status_text(
                status_text=f'Colour {primary_colour} assigned to palette entry {palette_button_id + 1}.')
            self.keystone_colour = primary_colour
        self.populate_harmony_colours()

    @log_call
    def populate_harmony_colours(self):
        log.log_debug(log_text='Populate harmony colours',
                      class_name='HarmonicsDialog',
                      method_name='populate_harmony_colours')
        primary_colour = self.keystone_colour
        harmony_method = self.opm_harmony_method.get()
        colour_object = ch.Color(mod.hex_to_rgb(self.keystone_colour), "", "")

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
            harmony_colour = mod.rgb_to_hex(colour)
            self.rendered_harmony_buttons[btn_idx].configure(fg_color=harmony_colour,
                                                             hover_color=harmony_colour)
        self.render_keystone_shades_palette(keystone_colour=primary_colour, harmony_method=harmony_method)

    @log_call
    def save_harmonics_geometry(self):
        """Save the harmonics panel geometry to the repo, for the next time the dialog is launched."""
        log.log_debug(log_text='Save harmonics display geometry',
                      class_name='HarmonicsDialog',
                      method_name='save_harmonics_geometry')
        geometry_row = pref.preference_row(db_file_path=DB_FILE_PATH,
                                           scope='window_geometry',
                                           preference_name='harmonics_panel')
        panel_geometry = self.geometry()
        geometry_row["preference_value"] = panel_geometry
        pref.upsert_preference(db_file_path=DB_FILE_PATH, preference_row_dict=geometry_row)

    @log_call
    def close_harmonics(self, event=None):
        log.log_debug(log_text=f'Closing colour harmonics dialogue',
                      class_name='HarmonicsDialog', method_name='close_harmonics')

        self.rendered_keystone_shades = []
        self.save_harmonics_geometry()
        self.destroy()
        self.harmony_palette_running = False
        self.master.set_option_states()

    @log_call
    def switch_harmony_method(self, event='event'):
        """This method updates the rendered buttons, below the keystone colour button, when we change the harmony
        method (complimentary, triadic etc)."""
        harmony_method = self.opm_harmony_method.get()
        log.log_debug(log_text='Update the newly generated colours to buttons, below the keystone colour button',
                      class_name='HarmonicsDialog',
                      method_name='switch_harmony_method')
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
            self.geometry(f"600x{self.HARMONICS_HEIGHT1}")
        elif harmony_entries == 2:
            self.geometry(f"650x{self.HARMONICS_HEIGHT2}")
        elif harmony_entries == 3:
            self.geometry(f"760x{self.HARMONICS_HEIGHT3}")

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

    @log_call
    def render_keystone_shades_palette(self, keystone_colour: str, harmony_method: str):
        """Render the "shades palette" (right hand side), which displays the keystone colour, the complementary colours,
        and the contrast shades. """
        colour_object = ch.Color(mod.hex_to_rgb(keystone_colour), "", "")

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
            harmony_colour = mod.rgb_to_hex(colour)
            harmony_colours_list.append(harmony_colour)
        else:
            for colour in harmony_colours:
                harmony_colour = mod.rgb_to_hex(tuple(colour))
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

    @log_call
    def copy_harmonics_to_palette(self):
        """This method copies the primary, and generated base colours to the first few tiles of the theme palette."""
        log.log_debug(log_text='Copy harmonics to theme colour palette',
                      class_name='HarmonicsDialog',
                      method_name='copy_harmonics_to_palette')
        harmonic_differential = self.harmony_contrast_differential
        colour_range = [self.btn_keystone_colour.cget('fg_color')]

        for btn_idx in range(len(self.rendered_harmony_buttons)):
            colour = self.rendered_harmony_buttons[btn_idx].cget('fg_color')
            colour_range.append(colour)
        num_harmony_colours = len(colour_range)

        harmony_idx = 0
        contrast_step = 0

        for idx in range(num_harmony_colours):

            colour = colour_range[harmony_idx]
            colour = cbtk.contrast_colour(colour, contrast_step * harmonic_differential)
            # We want to copy the gemerated colours to the "scratch" tile locations. These are
            # the 1st two tiles (actually buttons) on each of the two palette rows, so...

            self.master.set_palette_colour(palette_button_id=idx, colour=colour)

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

        self.master.json_state = 'dirty'
        self.master.set_option_states()

    @log_call
    def tag_keystone_colour_to_theme(self):
        """Tag the keystone colour, and harmony method, to the theme."""
        keystone_colour = self.btn_keystone_colour.cget('fg_color')
        harmony_method = self.opm_harmony_method.get()
        log.log_debug(log_text='Tag the keystone colour, and harmony method, to the theme',
                      class_name='HarmonicsDialog',
                      method_name='copy_harmonics_to_palette')
        self.theme_json_data['provenance']['keystone colour'] = keystone_colour
        self.theme_json_data['provenance']['harmony method'] = harmony_method
        self.theme_json_data['provenance']['harmony differential'] = self.harmony_contrast_differential
        self.master.json_state = 'dirty'
        self.master.set_option_states()
        self.harmony_status_bar.set_status_text(
            status_text=f'Keystone colour tagged to theme {self.theme_name}.')
