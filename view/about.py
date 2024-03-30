"""" Class container for the About dialogue. """

import model.ctk_theme_builder as mod
from model.ctk_theme_builder import log_call

import customtkinter as ctk
import tkinter as tk
import utils.cbtk_kit as cbtk
import utils.loggerutl as log

APP_IMAGES = mod.APP_IMAGES

class About(ctk.CTkToplevel):
    """About application pop-up dialogue class."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        icon_photo = tk.PhotoImage(file=APP_IMAGES / 'bear-logo-colour-dark.png')
        self.iconphoto(False, icon_photo)

        widget_corner_radius = 5
        self.title('About CTk Theme Builder')
        logo_image = cbtk.load_image(light_image=APP_IMAGES / 'bear-logo-colour.jpg', image_size=(200, 200))
        # Make preferences dialog modal
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.columnconfigure(0, weight=1)

        frm_main = ctk.CTkFrame(master=self, corner_radius=widget_corner_radius, border_width=0)
        frm_main.grid(column=0, row=0, sticky='nsew')
        frm_main.columnconfigure(1, weight=1)
        frm_main.rowconfigure(0, weight=1)
        frm_main.rowconfigure(1, weight=0)

        frm_widgets = ctk.CTkFrame(master=frm_main, corner_radius=widget_corner_radius, border_width=0)
        frm_widgets.grid(column=0, row=0, padx=10, pady=10, sticky='nsew')

        frm_logo = ctk.CTkFrame(master=frm_main, corner_radius=widget_corner_radius, border_width=0)
        frm_logo.grid(column=1, row=0, padx=10, pady=10, sticky='nsew')

        app_title = mod.app_title()
        app_version = mod.app_version()
        lbl_title = ctk.CTkLabel(master=frm_widgets, text=f'{app_title}:  {app_version}')
        lbl_title.grid(row=0, column=0, padx=(10, 10), pady=(35, 10), sticky='ew')

        lbl_ctk_version = ctk.CTkLabel(master=frm_widgets, text=f'CustomTkinter:  {ctk.__version__}')
        lbl_ctk_version.grid(row=2, column=0, padx=10, pady=(0, 10), sticky='w')

        app_author = mod.app_author()
        lbl_author = ctk.CTkLabel(master=frm_widgets, text=f'Author:  {app_author}')
        lbl_author.grid(row=3, column=0, padx=10, pady=(0, 10), sticky='w')

        lbl_author = ctk.CTkLabel(master=frm_widgets, text=f'Logo:  Jan Bajec')
        lbl_author.grid(row=4, column=0, padx=10, pady=(0, 10), sticky='w')

        btn_logo = ctk.CTkButton(master=frm_logo, text='', height=50, width=50, corner_radius=widget_corner_radius,
                                 image=logo_image)
        btn_logo.grid(row=0, column=1, sticky='w')

        frm_buttons = ctk.CTkFrame(master=frm_main, corner_radius=widget_corner_radius, border_width=0)
        frm_buttons.grid(column=0, row=1, padx=(5, 5), pady=(0, 0), sticky='ew', columnspan=2)

        btn_ok = ctk.CTkButton(master=frm_buttons, text='OK', width=400, border_width=0,
                               corner_radius=widget_corner_radius,
                               command=self.close_dialog)
        btn_ok.grid(row=0, column=0, padx=(5, 5), pady=10)

        self.grab_set()
        self.lift()
        self.bind('<Escape>', self.close_dialog)

    @log_call
    def close_dialog(self, event=None):
        log.log_debug(log_text='Closing About dialogue',
                      class_name='About', method_name='close_dialog')
        self.destroy()
