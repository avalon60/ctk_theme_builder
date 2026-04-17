"""Reusable colour drag-and-drop support for swatch buttons."""

# Author: Clive Bostock
# Date: 2026-04-17
# Description: Provides a ghost-swatch drag manager and drop adapters for palette and mapping swatches.

from __future__ import annotations

import math
import tkinter as tk
from dataclasses import dataclass
from typing import Callable

import customtkinter as ctk

import ctk_tb.utils.cbtk_kit as cbtk
import ctk_tb.utils.loggerutl as log

SHIFT_MASK = 0x0001
DRAG_THRESHOLD_PX = 6
GHOST_SIZE_PX = 20
GHOST_OFFSET_X = 16
GHOST_OFFSET_Y = 16


@dataclass
class HighlightState:
    """Stores the original border styling for a highlighted swatch."""

    border_color: str | tuple[str, str]
    border_width: int | str


class BaseColourSwatchAdapter:
    """Expose a CTkButton swatch through a small colour drag/drop protocol."""

    def __init__(
        self,
        controller,
        widget: ctk.CTkButton,
        click_callback: Callable[[tk.Event | None], None] | None = None,
    ) -> None:
        self.controller = controller
        self.widget = widget
        self.click_callback = click_callback
        self._highlight_state: HighlightState | None = None
        self._install_protocol()

    def _install_protocol(self) -> None:
        """Attach the colour drag/drop protocol to the widget instance."""
        self.widget.get_colour = self.get_colour
        self.widget.handle_colour_drop = self.handle_colour_drop
        self.widget._colour_drag_adapter = self

    def handle_click(self, event: tk.Event | None = None) -> None:
        """Invoke the normal single-click action if one is configured."""
        if self.click_callback is not None:
            self.click_callback(event)

    def is_same_target(self, other_widget) -> bool:
        """Return True when two widgets represent the same swatch target."""
        return other_widget is self.widget

    def get_colour(self) -> str:
        """Return the currently displayed swatch colour."""
        return str(self.widget.cget("fg_color"))

    def accepts_colour_drop(self) -> bool:
        """Return True when the swatch should be considered a drop target."""
        return True

    def apply_colour(self, hex_colour: str) -> None:
        """Apply a colour using the owning controller's existing update path."""
        raise NotImplementedError

    def set_drop_highlight(self, active: bool) -> None:
        """Toggle a lightweight border highlight during drag hover."""
        if not self.widget.winfo_exists():
            return

        if active:
            if self._highlight_state is None:
                self._highlight_state = HighlightState(
                    border_color=self.widget.cget("border_color"),
                    border_width=self.widget.cget("border_width"),
                )
            highlight_colour = cbtk.contrast_colour(self.get_colour(), 55)
            try:
                border_width = int(self.widget.cget("border_width"))
            except (TypeError, ValueError):
                border_width = 2
            self.widget.configure(
                border_color=highlight_colour,
                border_width=max(border_width, 3),
            )
            return

        if self._highlight_state is None:
            return
        self.widget.configure(
            border_color=self._highlight_state.border_color,
            border_width=self._highlight_state.border_width,
        )
        self._highlight_state = None

    def handle_colour_drop(self, hex_colour: str, source_widget, drag_mode: str) -> None:
        """Accept a dropped colour, copying or swapping via existing controller methods."""
        source_adapter = getattr(source_widget, "_colour_drag_adapter", None)
        if source_adapter is None or source_adapter.is_same_target(self.widget):
            return

        if drag_mode == "swap":
            target_colour = self.get_colour()
            self.apply_colour(hex_colour)
            source_adapter.apply_colour(target_colour)
            return

        self.apply_colour(hex_colour)


class PaletteSwatchAdapter(BaseColourSwatchAdapter):
    """Adapter for theme palette swatch buttons."""

    def __init__(
        self,
        controller,
        widget: ctk.CTkButton,
        palette_button_id: int,
        click_callback: Callable[[tk.Event | None], None] | None = None,
    ) -> None:
        self.palette_button_id = palette_button_id
        super().__init__(controller=controller, widget=widget, click_callback=click_callback)

    def apply_colour(self, hex_colour: str) -> None:
        """Update the palette swatch through the normal palette flow."""
        self.controller.paste_palette_colour(
            event=None,
            palette_button_id=self.palette_button_id,
            property_colour=hex_colour,
        )


class MappingSwatchAdapter(BaseColourSwatchAdapter):
    """Adapter for colour-mapping swatch buttons."""

    def __init__(
        self,
        controller,
        widget: ctk.CTkButton,
        widget_property: str,
        click_callback: Callable[[tk.Event | None], None] | None = None,
    ) -> None:
        self.widget_property = widget_property
        super().__init__(controller=controller, widget=widget, click_callback=click_callback)

    def apply_colour(self, hex_colour: str) -> None:
        """Update the mapping swatch through the normal widget-colour flow."""
        self.controller.paste_colour(
            event=None,
            widget_property=self.widget_property,
            property_colour=hex_colour,
        )


class ReadOnlyColourSwatchAdapter(BaseColourSwatchAdapter):
    """Adapter for swatches that can be dragged from but should not accept drops."""

    def accepts_colour_drop(self) -> bool:
        """Treat this swatch as source-only."""
        return False

    def apply_colour(self, hex_colour: str) -> None:
        """Allow swap fallback to repaint the source swatch when explicitly requested."""
        hover_colour = cbtk.contrast_colour(hex_colour)
        self.widget.configure(fg_color=hex_colour, hover_color=hover_colour)


class HarmonyKeystoneSwatchAdapter(BaseColourSwatchAdapter):
    """Adapter for the harmonics keystone swatch."""

    def apply_colour(self, hex_colour: str) -> None:
        """Update the harmonics keystone via the dialog's normal regeneration flow."""
        harmony_method = self.controller.opm_harmony_method.get()
        self.controller.set_harmony_keystone(colour_code=hex_colour, method=harmony_method)
        self.controller.populate_harmony_colours()
        self.controller.harmony_status_bar.set_status_text(
            status_text=f"Colour {hex_colour} assigned."
        )


class ColourSwatchDragManager:
    """Manage ghost-swatch dragging across palette and mapping swatches."""

    def __init__(self, root: tk.Misc) -> None:
        self.root = root
        self._source_widget = None
        self._press_root_x = 0
        self._press_root_y = 0
        self._drag_started = False
        self._ghost_window: ctk.CTkToplevel | None = None
        self._ghost_frame: ctk.CTkFrame | None = None
        self._highlighted_adapter: BaseColourSwatchAdapter | None = None

    def register_swatch(self, widget: ctk.CTkButton) -> None:
        """Bind drag gestures to a swatch widget exposing the colour-drop protocol."""
        widget.bind("<ButtonPress-1>", self._on_button_press)
        widget.bind("<B1-Motion>", self._on_drag_motion)
        widget.bind("<ButtonRelease-1>", self._on_button_release)
        widget.bind("<Destroy>", self._on_widget_destroy)

    def _on_button_press(self, event: tk.Event) -> None:
        source_adapter = self._resolve_adapter(event.widget)
        self._source_widget = source_adapter.widget if source_adapter is not None else None
        self._press_root_x = event.x_root
        self._press_root_y = event.y_root
        self._drag_started = False

    def _on_drag_motion(self, event: tk.Event) -> None:
        if self._source_widget is None or not self._widget_exists(self._source_widget):
            self._cleanup_drag_state()
            return

        if not self._drag_started and not self._drag_threshold_exceeded(event):
            return

        if not self._drag_started:
            self._drag_started = True
            self._create_ghost(self._source_widget.get_colour())

        self._move_ghost(event.x_root, event.y_root)
        self._update_drop_highlight(event.x_root, event.y_root)

    def _on_button_release(self, event: tk.Event) -> None:
        source_widget = self._source_widget
        drag_started = self._drag_started

        try:
            if source_widget is None or not self._widget_exists(source_widget):
                return

            if not drag_started:
                source_adapter = getattr(source_widget, "_colour_drag_adapter", None)
                if source_adapter is not None:
                    source_adapter.handle_click(event)
                return

            target_widget = self.root.winfo_containing(event.x_root, event.y_root)
            target_adapter = self._resolve_drop_adapter(target_widget)
            if target_adapter is None or target_adapter.is_same_target(source_widget):
                return

            drag_mode = self._drag_mode(event)
            target_adapter.handle_colour_drop(
                hex_colour=source_widget.get_colour(),
                source_widget=source_widget,
                drag_mode=drag_mode,
            )
        except Exception as exc:  # pragma: no cover - defensive GUI cleanup path
            log.log_warning(
                log_text=f"Colour drag/drop failed: {exc}",
                class_name="ColourSwatchDragManager",
                method_name="_on_button_release",
            )
        finally:
            self._cleanup_drag_state()

    def _on_widget_destroy(self, event: tk.Event) -> None:
        if event.widget is self._source_widget:
            self._cleanup_drag_state()
            return

        adapter = getattr(event.widget, "_colour_drag_adapter", None)
        if adapter is not None and adapter is self._highlighted_adapter:
            self._highlighted_adapter = None

    def _drag_threshold_exceeded(self, event: tk.Event) -> bool:
        delta_x = event.x_root - self._press_root_x
        delta_y = event.y_root - self._press_root_y
        return math.hypot(delta_x, delta_y) >= DRAG_THRESHOLD_PX

    def _drag_mode(self, event: tk.Event) -> str:
        return "swap" if event.state & SHIFT_MASK else "copy"

    def _create_ghost(self, hex_colour: str) -> None:
        if self._ghost_window is not None:
            return

        ghost = ctk.CTkToplevel(self.root)
        ghost.overrideredirect(True)
        ghost.attributes("-topmost", True)
        try:
            ghost.attributes("-alpha", 0.7)
        except tk.TclError:
            pass

        frame = ctk.CTkFrame(
            master=ghost,
            width=GHOST_SIZE_PX,
            height=GHOST_SIZE_PX,
            fg_color=hex_colour,
            corner_radius=4,
            border_width=1,
            border_color=cbtk.contrast_colour(hex_colour, 55),
        )
        frame.pack(fill="both", expand=True)
        frame.pack_propagate(False)

        self._ghost_window = ghost
        self._ghost_frame = frame

    def _move_ghost(self, x_root: int, y_root: int) -> None:
        if self._ghost_window is None:
            return
        self._ghost_window.geometry(
            f"{GHOST_SIZE_PX}x{GHOST_SIZE_PX}+{x_root + GHOST_OFFSET_X}+{y_root + GHOST_OFFSET_Y}"
        )

    def _update_drop_highlight(self, x_root: int, y_root: int) -> None:
        target_widget = self.root.winfo_containing(x_root, y_root)
        target_adapter = self._resolve_drop_adapter(target_widget)

        if target_adapter is self._highlighted_adapter:
            return

        if self._highlighted_adapter is not None:
            self._highlighted_adapter.set_drop_highlight(False)
            self._highlighted_adapter = None

        if target_adapter is None:
            return

        if self._source_widget is not None and target_adapter.is_same_target(self._source_widget):
            return

        target_adapter.set_drop_highlight(True)
        self._highlighted_adapter = target_adapter

    def _resolve_drop_adapter(self, widget) -> BaseColourSwatchAdapter | None:
        adapter = self._resolve_adapter(widget)
        if adapter is None or not adapter.accepts_colour_drop():
            return None
        return adapter

    def _resolve_adapter(self, widget) -> BaseColourSwatchAdapter | None:
        current = widget
        while current is not None:
            adapter = getattr(current, "_colour_drag_adapter", None)
            if adapter is not None:
                return adapter
            current = getattr(current, "master", None)
        return None

    def _cleanup_drag_state(self) -> None:
        if self._highlighted_adapter is not None:
            self._highlighted_adapter.set_drop_highlight(False)
            self._highlighted_adapter = None

        if self._ghost_window is not None:
            try:
                self._ghost_window.destroy()
            except tk.TclError:
                pass

        self._ghost_window = None
        self._ghost_frame = None
        self._source_widget = None
        self._drag_started = False

    @staticmethod
    def _widget_exists(widget) -> bool:
        try:
            return bool(widget.winfo_exists())
        except tk.TclError:
            return False
