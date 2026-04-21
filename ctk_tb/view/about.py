"""About dialog for CTk Theme Builder."""

# Author: Clive Bostock
# Date: 2026-04-21
# Description: Displays application metadata and performs a best-effort PyPI update check.

import json
import sys
import threading
import tkinter as tk
import urllib.error
import urllib.request

import customtkinter as ctk
from packaging.version import InvalidVersion
from packaging.version import Version

import ctk_tb.model.ctk_theme_builder as mod
import ctk_tb.utils.cbtk_kit as cbtk
import ctk_tb.utils.loggerutl as log
from ctk_tb.model.ctk_theme_builder import log_call

APP_IMAGES = mod.APP_IMAGES
PYPI_PROJECT_JSON_URL = 'https://pypi.org/pypi/ctk-theme-builder/json'
PYPI_TIMEOUT_S = 2.5
_UPDATE_CHECK_CACHE: tuple[bool, str] | None = None


def _fetch_update_status(current_version: str, timeout_s: float = PYPI_TIMEOUT_S) -> tuple[bool, str] | None:
    """Return update availability and latest version from PyPI when reachable.

    Args:
        current_version: The version currently running in the application.
        timeout_s: Timeout for the PyPI request in seconds.

    Returns:
        A tuple of ``(update_available, latest_version)`` when the lookup
        succeeds, otherwise ``None``.
    """
    global _UPDATE_CHECK_CACHE

    if _UPDATE_CHECK_CACHE is not None:
        return _UPDATE_CHECK_CACHE

    try:
        with urllib.request.urlopen(PYPI_PROJECT_JSON_URL, timeout=timeout_s) as response:
            payload = json.load(response)
        latest_version = payload['info']['version']
        update_available = Version(latest_version) > Version(current_version)
    except (OSError, ValueError, KeyError, InvalidVersion, urllib.error.URLError) as error:
        log.log_debug(
            log_text=f'About dialog update check unavailable: {error}',
            class_name='About',
            method_name='_fetch_update_status',
        )
        return None

    _UPDATE_CHECK_CACHE = (update_available, latest_version)
    return _UPDATE_CHECK_CACHE


class About(ctk.CTkToplevel):
    """About application pop-up dialogue class."""

    def __init__(self, *args, **kwargs):
        """Initialise the About dialog and start the background update check."""
        super().__init__(*args, **kwargs)

        self.icon_photo = tk.PhotoImage(file=APP_IMAGES / 'ctk-tb-ico-taskbar.png')
        self.iconphoto(False, self.icon_photo)

        widget_corner_radius = 5
        self.app_version = mod.app_version()
        self.logo_image = cbtk.load_image(light_image=APP_IMAGES / 'bear-logo-colour.jpg', image_size=(200, 200))
        self.title('About CTk Theme Builder')

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
        lbl_title = ctk.CTkLabel(master=frm_widgets, text=f'{app_title}:  {self.app_version}')
        lbl_title.grid(row=0, column=0, padx=(10, 10), pady=(35, 10), sticky='ew')

        self.tk_update_status = tk.StringVar(value='Checking for updates...')
        self.lbl_update_status = ctk.CTkLabel(
            master=frm_widgets,
            textvariable=self.tk_update_status,
            justify='left',
            wraplength=320,
        )
        self.lbl_update_status.grid(row=1, column=0, padx=10, pady=(0, 10), sticky='w')

        lbl_ctk_version = ctk.CTkLabel(master=frm_widgets, text=f'CustomTkinter:  {ctk.__version__}')
        lbl_ctk_version.grid(row=2, column=0, padx=10, pady=(0, 10), sticky='w')

        lbl_python_version = ctk.CTkLabel(
            master=frm_widgets,
            text=f'Python:  {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}',
        )
        lbl_python_version.grid(row=3, column=0, padx=10, pady=(0, 10), sticky='w')

        app_author = mod.app_author()
        lbl_author = ctk.CTkLabel(master=frm_widgets, text=f'Author:  {app_author}')
        lbl_author.grid(row=4, column=0, padx=10, pady=(0, 10), sticky='w')

        lbl_logo_credit = ctk.CTkLabel(master=frm_widgets, text='Logo:  Jan Bajec')
        lbl_logo_credit.grid(row=5, column=0, padx=10, pady=(0, 10), sticky='w')

        btn_logo = ctk.CTkButton(
            master=frm_logo,
            text='',
            height=50,
            width=50,
            corner_radius=widget_corner_radius,
            image=self.logo_image,
        )
        btn_logo.grid(row=0, column=1, sticky='w')

        frm_buttons = ctk.CTkFrame(master=frm_main, corner_radius=widget_corner_radius, border_width=0)
        frm_buttons.grid(column=0, row=1, padx=(5, 5), pady=(0, 0), sticky='ew', columnspan=2)

        btn_ok = ctk.CTkButton(
            master=frm_buttons,
            text='OK',
            width=400,
            border_width=0,
            corner_radius=widget_corner_radius,
            command=self.close_dialog,
        )
        btn_ok.grid(row=0, column=0, padx=(5, 5), pady=10)

        self.grab_set()
        self.lift()
        self.bind('<Escape>', self.close_dialog)
        self._start_update_check()

    def _start_update_check(self) -> None:
        """Start a background update check so the dialog stays responsive."""
        worker = threading.Thread(target=self._check_for_updates, daemon=True)
        worker.start()

    def _check_for_updates(self) -> None:
        """Fetch update information from PyPI and marshal the result back to Tk."""
        update_status = _fetch_update_status(self.app_version)
        if not self.winfo_exists():
            return
        self.after(0, lambda: self._apply_update_status(update_status))

    def _apply_update_status(self, update_status: tuple[bool, str] | None) -> None:
        """Render the update-check result in the dialog."""
        if not self.winfo_exists():
            return

        if update_status is None:
            self.tk_update_status.set('')
            return

        update_available, latest_version = update_status
        if update_available:
            self.tk_update_status.set(f'Update available: {latest_version}')
        else:
            self.tk_update_status.set('You are up to date.')

    @log_call
    def close_dialog(self, event=None):
        """Close the About dialog."""
        log.log_debug(log_text='Closing About dialogue',
                      class_name='About', method_name='close_dialog')
        self.destroy()
