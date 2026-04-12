"""Compatibility helpers for third-party tooltip bindings."""

# Author: Clive Bostock
# Date: 2026-04-11
# Description: Applies local compatibility patches for CTkToolTip event bindings.

from __future__ import annotations


def patch_ctk_tooltip_destroy_binding() -> None:
    """Patch CTkToolTip so its destroy binding tolerates calls without an event.

    Recent callback paths can invoke the stored destroy callback without passing
    an event object. The upstream CTkToolTip binding uses ``lambda _: ...``,
    which raises ``TypeError`` in that case. This patch widens the callback
    signature to accept zero or more positional arguments.
    """
    try:
        import customtkinter
        import sys
        from tkinter import Frame
        from CTkToolTip import CTkToolTip
    except ImportError:
        return

    if getattr(CTkToolTip, "_ctk_tb_destroy_binding_patched", False):
        return

    original_init = CTkToolTip.__init__

    def patched_init(
            self,
            widget=None,
            message=None,
            delay: float = 0.2,
            follow: bool = True,
            x_offset: int = +20,
            y_offset: int = +10,
            bg_color: str = None,
            corner_radius: int = 10,
            border_width: int = 0,
            border_color: str = None,
            alpha: float = 0.95,
            padding: tuple = (10, 2),
            **message_kwargs):
        super(CTkToolTip, self).__init__()

        self.widget = widget

        self.withdraw()
        self.overrideredirect(True)

        if sys.platform.startswith("win"):
            self.transparent_color = self.widget._apply_appearance_mode(
                customtkinter.ThemeManager.theme["CTkToplevel"]["fg_color"])
            self.attributes("-transparentcolor", self.transparent_color)
            self.transient()
        elif sys.platform.startswith("darwin"):
            self.transparent_color = "systemTransparent"
            self.attributes("-transparent", True)
            self.transient(self.master)
        else:
            self.transparent_color = "#000001"
            corner_radius = 0
            self.transient()

        self.resizable(width=True, height=True)
        self.config(background=self.transparent_color)

        self.messageVar = customtkinter.StringVar()
        self.message = message
        self.messageVar.set(self.message)

        self.delay = delay
        self.follow = follow
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.corner_radius = corner_radius
        self.alpha = alpha
        self.border_width = border_width
        self.padding = padding
        self.bg_color = customtkinter.ThemeManager.theme["CTkFrame"]["fg_color"] if bg_color is None else bg_color
        self.border_color = border_color
        self.disable = False

        self.status = "outside"
        self.last_moved = 0
        self.attributes("-alpha", self.alpha)

        if sys.platform.startswith("win"):
            if self.widget._apply_appearance_mode(self.bg_color) == self.transparent_color:
                self.transparent_color = "#000001"
                self.config(background=self.transparent_color)
                self.attributes("-transparentcolor", self.transparent_color)

        self.transparent_frame = Frame(self, bg=self.transparent_color)
        self.transparent_frame.pack(padx=0, pady=0, fill="both", expand=True)

        self.frame = customtkinter.CTkFrame(
            self.transparent_frame,
            bg_color=self.transparent_color,
            corner_radius=self.corner_radius,
            border_width=self.border_width,
            fg_color=self.bg_color,
            border_color=self.border_color,
        )
        self.frame.pack(padx=0, pady=0, fill="both", expand=True)

        self.message_label = customtkinter.CTkLabel(self.frame, textvariable=self.messageVar, **message_kwargs)
        self.message_label.pack(
            fill="both",
            padx=self.padding[0] + self.border_width,
            pady=self.padding[1] + self.border_width,
            expand=True,
        )

        if self.widget.winfo_name() != "tk":
            if self.frame.cget("fg_color") == self.widget.cget("bg_color"):
                if not bg_color:
                    self._top_fg_color = self.frame._apply_appearance_mode(
                        customtkinter.ThemeManager.theme["CTkFrame"]["top_fg_color"])
                    if self._top_fg_color != self.transparent_color:
                        self.frame.configure(fg_color=self._top_fg_color)

        self.widget.bind("<Enter>", self.on_enter, add="+")
        self.widget.bind("<Leave>", self.on_leave, add="+")
        self.widget.bind("<Motion>", self.on_enter, add="+")
        self.widget.bind("<B1-Motion>", self.on_enter, add="+")
        self.widget.bind("<Destroy>", lambda *_: self.hide(), add="+")

    CTkToolTip.__init__ = patched_init
    CTkToolTip._ctk_tb_destroy_binding_patched = True

