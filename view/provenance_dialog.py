"""Class container for ProvenanceDiaglog"""

import customtkinter as ctk
import tkinter as tk
import model.ctk_theme_builder as mod
from model.ctk_theme_builder import log_call
import utils.cbtk_kit as cbtk
import utils.loggerutl as log

APP_IMAGES = mod.APP_IMAGES

HEADING1 = mod.HEADING1
HEADING2 = mod.HEADING2
HEADING3 = mod.HEADING3
HEADING4 = mod.HEADING4

REGULAR_TEXT = cbtk.REGULAR_TEXT
SMALL_TEXT = mod.SMALL_TEXT


class ProvenanceDialog(ctk.CTkToplevel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title('Theme Provenance')
        # self.geometry('520x470')
        # Make sure we pop up in front of Control Panel
        icon_photo = tk.PhotoImage(file=APP_IMAGES / 'bear-logo-colour-dark.png')
        self.iconphoto(False, icon_photo)
        self.rowconfigure(1, weight=1)

        frm_header = ctk.CTkFrame(master=self)
        frm_header.grid(column=0, row=0, padx=5, pady=5, sticky='nsew')

        frm_widgets = ctk.CTkFrame(master=self)
        frm_widgets.grid(column=0, row=1, padx=5, pady=5, sticky='nsew')

        frm_buttons = ctk.CTkFrame(master=self)
        frm_buttons.grid(column=0, row=2, padx=5, pady=5, sticky='ew')

        widget_row = 0
        # Header -  Theme Name (frm_header)
        lbl_theme_label = ctk.CTkLabel(master=frm_header, text='Theme:', width=280, anchor="e", font=HEADING4)
        lbl_theme_label.grid(row=widget_row, column=0, padx=5, pady=10, sticky='e', columnspan=2)

        self.lbl_theme_name = ctk.CTkLabel(master=frm_header, justify="left", font=HEADING4)
        self.lbl_theme_name.grid(row=widget_row, column=2, padx=5, pady=10, sticky='w', columnspan=2)

        # Start the main body of the dialog (frm_widgets)
        # Creation Details
        widget_row += 1
        lbl_author_label = ctk.CTkLabel(master=frm_widgets, text='Author:', anchor="e", width=75)
        lbl_author_label.grid(row=widget_row, column=0, padx=20, pady=10, sticky='e')

        self.lbl_author_name = ctk.CTkLabel(master=frm_widgets, anchor="w")
        self.lbl_author_name.grid(row=widget_row, column=1, padx=5, pady=10, sticky='w')

        lbl_created_label = ctk.CTkLabel(master=frm_widgets, text='Created:', width=100, anchor="e")
        lbl_created_label.grid(row=widget_row, column=2, padx=5, pady=10, sticky='e')

        self.lbl_created_date = ctk.CTkLabel(master=frm_widgets, anchor="w", width=75)
        self.lbl_created_date.grid(row=widget_row, column=3, padx=(20, 30), pady=10, sticky='w')

        # Modification Details
        widget_row += 1
        lbl_modified_by_label = ctk.CTkLabel(master=frm_widgets, text='Last modified:', anchor="e")
        lbl_modified_by_label.grid(row=widget_row, column=0, padx=20, pady=10, sticky='e')

        self.lbl_modified_by_name = ctk.CTkLabel(master=frm_widgets, anchor="w")
        self.lbl_modified_by_name.grid(row=widget_row, column=1, padx=5, pady=10, sticky='w')

        lbl_last_modified_label = ctk.CTkLabel(master=frm_widgets, text='Date:', width=75, anchor="e")
        lbl_last_modified_label.grid(row=widget_row, column=2, padx=5, pady=10, sticky='e')

        self.lbl_last_modified_date = ctk.CTkLabel(master=frm_widgets, anchor="w")
        self.lbl_last_modified_date.grid(row=widget_row, column=3, padx=20, pady=10, sticky='w')

        # Keystone Details
        widget_row += 1
        lbl_keystone_method_label = ctk.CTkLabel(master=frm_widgets, text='Harmony method:', width=75, anchor="e")
        lbl_keystone_method_label.grid(row=widget_row, column=0, padx=20, pady=10, sticky='e')

        self.lbl_harmony_method = ctk.CTkLabel(master=frm_widgets, anchor="w")
        self.lbl_harmony_method.grid(row=widget_row, column=1, padx=5, pady=10, sticky='w')

        widget_row += 1
        lbl_keystone_colour_label = ctk.CTkLabel(master=frm_widgets, text='Keystone colour:', width=75, anchor="e")
        lbl_keystone_colour_label.grid(row=widget_row, column=0, padx=20, pady=10, sticky='e')

        self.lbl_keystone_colour = ctk.CTkLabel(master=frm_widgets, anchor="w")
        self.lbl_keystone_colour.grid(row=widget_row, column=1, padx=5, pady=(10, 5), sticky='w')

        widget_row += 1
        self.btn_keystone_colour = ctk.CTkButton(master=frm_widgets,
                                                 height=70,
                                                 border_width=2,
                                                 width=50)
        self.btn_keystone_colour.grid(row=widget_row, column=1, padx=5, pady=(0, 5), sticky='w')

        # Created with...
        regular_italic = ctk.CTkFont(family="Roboto", size=13, slant="italic")
        widget_row += 1
        lbl_created_with_label = ctk.CTkLabel(master=frm_widgets, font=regular_italic,
                                              text='Built with:', width=75, anchor="e")
        lbl_created_with_label.grid(row=widget_row, column=2, padx=20, pady=(50, 10), sticky='e')

        self.lbl_created_with = ctk.CTkLabel(master=frm_widgets, font=regular_italic, anchor="w")
        self.lbl_created_with.grid(row=widget_row, column=3, padx=5, pady=(50, 10), sticky='w')

        # Add the close button into the bottom frame (frm_buttons).
        btn_close = ctk.CTkButton(master=frm_buttons, text='Close', command=self.close_dialog, width=550)
        self.grab_set()
        self.lift()
        btn_close.grid(row=0, column=0, padx=10, pady=(5, 5), sticky='we')
        self.bind('<Escape>', self.close_dialog)

    @log_call
    def close_dialog(self, event=None):
        log.log_debug(log_text='Close provenance dialogue', class_name='ProvenanceDialog',
                      method_name='close_dialog')
        self.destroy()

    @log_call
    def modify_property(self, property_name, value):
        if property_name == "theme_name":
            self.lbl_theme_name.configure(text=value)
        elif property_name == "created_with":
            self.lbl_created_with.configure(text=value)
        elif property_name == "date_created":
            self.lbl_created_date.configure(text=value)
        elif property_name == 'created_with':
            self.lbl_created_with.configure(text=value)
        elif property_name == 'created_date':
            self.lbl_created_date.configure(text=value)
        elif property_name == 'authors_name':
            self.lbl_author_name.configure(text=value)
        elif property_name == 'last_modified_by':
            self.lbl_modified_by_name.configure(text=value)
        elif property_name == 'last_modified_date':
            self.lbl_last_modified_date.configure(text=value)
        elif property_name == 'harmony_method':
            self.lbl_harmony_method.configure(text=value)
        elif property_name == 'keystone_colour':
            self.lbl_keystone_colour.configure(text=value)
            self.btn_keystone_colour.configure(fg_color=value, hover_color=value, text=value)
