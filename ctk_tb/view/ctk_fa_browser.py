"""CustomTkinter browser for Font Awesome icons."""

import customtkinter as ctk
import tkinter as tk

import ctkfontawesome

import ctk_tb.model.ctk_theme_builder as mod
import ctk_tb.model.preferences as pref
import ctk_tb.utils.cbtk_kit as cbtk


APP_IMAGES = mod.APP_IMAGES
APP_THEMES_DIR = mod.APP_THEMES_DIR
DB_FILE_PATH = mod.DB_FILE_PATH
DEFAULT_GEOMETRY = "1040x680+120+80"


def browser_runtime_preferences():
    control_panel_theme = pref.preference_setting(
        db_file_path=DB_FILE_PATH,
        scope="user_preference",
        preference_name="control_panel_theme",
    )
    control_panel_mode = pref.preference_setting(
        db_file_path=DB_FILE_PATH,
        scope="user_preference",
        preference_name="control_panel_mode",
    )
    icon_browser_scaling = pref.preference_setting(
        db_file_path=DB_FILE_PATH,
        scope="scaling",
        preference_name="icon_browser",
    )
    if icon_browser_scaling == "NO_DATA_FOUND":
        icon_browser_scaling = "100%"
        scaling_row = pref.new_preference_dict(
            scope="scaling",
            preference_name="icon_browser",
            data_type="str",
            preference_value=icon_browser_scaling,
        )
        pref.upsert_preference(db_file_path=DB_FILE_PATH, preference_row_dict=scaling_row)
    return control_panel_theme, control_panel_mode, icon_browser_scaling


def configure_browser_runtime():
    control_panel_theme, control_panel_mode, icon_browser_scaling = browser_runtime_preferences()
    control_panel_theme_path = str(APP_THEMES_DIR / f"{control_panel_theme}.json")
    try:
        ctk.set_default_color_theme(control_panel_theme_path)
    except FileNotFoundError:
        pass
    ctk.set_appearance_mode(control_panel_mode)
    ctk.set_widget_scaling(mod.scaling_float(icon_browser_scaling))


class IconBrowser(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        configure_browser_runtime()
        super().__init__(*args, **kwargs)

        icon_photo = tk.PhotoImage(file=APP_IMAGES / "bear-logo-colour-dark.png")
        self.iconphoto(False, icon_photo)

        self.title("Browse Icons")
        self.protocol("WM_DELETE_WINDOW", self.close_dialog)
        self._restore_geometry()
        self.minsize(900, 560)

        self.all_icons = ctkfontawesome.icon_names()
        self.all_categories = ctkfontawesome.category_names()
        self.filtered_icons = self.all_icons[:]
        self.current_image = None
        self.current_name = None

        self.category_var = tk.StringVar(value="All categories")
        self.search_var = tk.StringVar()
        self.fill_var = tk.StringVar(value="#1f6aa5")
        self.size_var = tk.StringVar(value="96")
        self.status_var = tk.StringVar(value="Ready.")
        self.selected_name_var = tk.StringVar(value="Select an icon")
        self.category_picker = None
        self.category_picker_listbox = None
        self.category_picker_button = None
        self.category_picker_search_entry = None
        self.filtered_categories = ["All categories", *self.all_categories]

        self._build_ui()
        self._populate_icon_buttons()
        if self.filtered_icons:
            self._select_icon(self.filtered_icons[0])

        self.bind("<Escape>", self.close_dialog)

    def _build_ui(self):
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        left = ctk.CTkFrame(self, corner_radius=10)
        left.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(6, weight=1)

        ctk.CTkLabel(left, text="Icon Library", font=mod.HEADING3).grid(
            row=0, column=0, sticky="w", padx=12, pady=(12, 2)
        )
        ctk.CTkLabel(
            left,
            text="Filter by category, then search by name.",
            font=mod.REGULAR_TEXT,
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 10))

        ctk.CTkLabel(left, text="Category", font=mod.REGULAR_TEXT).grid(
            row=2, column=0, sticky="w", padx=12, pady=(0, 4)
        )
        self.category_picker_button = ctk.CTkButton(
            left,
            text=f"Category: {self.category_var.get()}",
            anchor="w",
            command=self._toggle_category_picker,
            width=280,
            height=34,
        )
        self.category_picker_button.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 8))

        search_entry = ctk.CTkEntry(left, textvariable=self.search_var, width=280)
        search_entry.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 8))
        search_entry.bind("<KeyRelease>", self._on_search)
        search_entry.focus()

        self.count_label = ctk.CTkLabel(left, text="", font=mod.REGULAR_TEXT)
        self.count_label.grid(row=5, column=0, sticky="w", padx=12, pady=(0, 6))

        self.icon_list_outer = ctk.CTkFrame(left, corner_radius=8)
        self.icon_list_outer.grid(row=6, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.icon_list_outer.columnconfigure(0, weight=1)
        self.icon_list_outer.rowconfigure(0, weight=1)

        self.icon_listbox = tk.Listbox(
            self.icon_list_outer,
            activestyle="none",
            borderwidth=0,
            highlightthickness=0,
            relief="flat",
            exportselection=False,
            selectmode=tk.SINGLE,
            background=self._listbox_background(),
            foreground=self._listbox_foreground(),
            selectbackground=self._listbox_selected_background(),
            selectforeground=self._listbox_selected_foreground(),
            font=mod.REGULAR_TEXT,
        )
        self.icon_listbox.grid(row=0, column=0, sticky="nsew")
        self.icon_listbox.bind("<<ListboxSelect>>", self._on_listbox_select)

        self.icon_scrollbar = ctk.CTkScrollbar(
            self.icon_list_outer,
            orientation="vertical",
            command=self.icon_listbox.yview,
        )
        self.icon_scrollbar.grid(row=0, column=1, sticky="ns")
        self.icon_listbox.configure(yscrollcommand=self.icon_scrollbar.set)

        right = ctk.CTkFrame(self, corner_radius=10)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(3, weight=1)

        header = ctk.CTkFrame(right, corner_radius=8)
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 10))
        header.columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="Selected Icon", font=mod.HEADING3).grid(
            row=0, column=0, sticky="w", padx=14, pady=(12, 2)
        )
        ctk.CTkLabel(header, textvariable=self.selected_name_var, font=mod.HEADING4).grid(
            row=1, column=0, sticky="w", padx=14, pady=(0, 12)
        )

        controls = ctk.CTkFrame(right, corner_radius=8)
        controls.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))
        controls.columnconfigure(7, weight=1)

        ctk.CTkLabel(controls, text="Fill").grid(row=0, column=0, sticky="w", padx=(12, 6), pady=(12, 8))
        fill_entry = ctk.CTkEntry(controls, textvariable=self.fill_var, width=110)
        fill_entry.grid(row=0, column=1, sticky="w", padx=(0, 12), pady=(12, 8))
        fill_entry.bind("<Return>", self._refresh_preview)

        ctk.CTkLabel(controls, text="Size").grid(row=0, column=2, sticky="w", padx=(0, 6), pady=(12, 8))
        size_entry = ctk.CTkEntry(controls, textvariable=self.size_var, width=70)
        size_entry.grid(row=0, column=3, sticky="w", padx=(0, 12), pady=(12, 8))
        size_entry.bind("<Return>", self._refresh_preview)

        ctk.CTkButton(controls, text="Refresh", width=90, command=self._refresh_preview).grid(
            row=0, column=4, sticky="w", padx=(0, 10), pady=(12, 8)
        )
        ctk.CTkButton(controls, text="Copy Name", width=100, command=self._copy_name).grid(
            row=0, column=5, sticky="w", padx=(0, 10), pady=(12, 8)
        )
        ctk.CTkButton(controls, text="Copy Code", width=100, command=self._copy_code).grid(
            row=0, column=6, sticky="w", padx=(0, 12), pady=(12, 8)
        )
        ctk.CTkLabel(
            controls,
            text="Tip: enter a hex fill colour and press Refresh to preview variants.",
            font=mod.REGULAR_TEXT,
            justify="left",
        ).grid(row=1, column=0, columnspan=7, sticky="w", padx=12, pady=(0, 12))

        self.preview_frame = ctk.CTkFrame(right, corner_radius=8)
        self.preview_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 10))
        self.preview_frame.columnconfigure(0, weight=1)
        self.preview_frame.columnconfigure(1, weight=1)
        self.preview_frame.rowconfigure(1, weight=1)

        ctk.CTkLabel(self.preview_frame, text="Preview", font=mod.HEADING4).grid(
            row=0, column=0, sticky="w", padx=14, pady=(12, 4), columnspan=2
        )

        self.preview_label = ctk.CTkLabel(self.preview_frame, text="", anchor="center", justify="center")
        self.preview_label.grid(row=1, column=0, sticky="nsew", padx=(14, 7), pady=(6, 14))

        self.preview_meta = ctk.CTkFrame(self.preview_frame, corner_radius=8)
        self.preview_meta.grid(row=1, column=1, sticky="nsew", padx=(7, 14), pady=(6, 14))
        self.preview_meta.columnconfigure(0, weight=1)

        ctk.CTkLabel(self.preview_meta, text="Preview Details", font=mod.HEADING4).grid(
            row=0, column=0, sticky="w", padx=14, pady=(12, 8)
        )
        self.meta_name = ctk.CTkLabel(self.preview_meta, text="", anchor="w", justify="left")
        self.meta_name.grid(row=1, column=0, sticky="w", padx=14, pady=4)
        self.meta_fill = ctk.CTkLabel(self.preview_meta, text="", anchor="w", justify="left")
        self.meta_fill.grid(row=2, column=0, sticky="w", padx=14, pady=4)
        self.meta_size = ctk.CTkLabel(self.preview_meta, text="", anchor="w", justify="left")
        self.meta_size.grid(row=3, column=0, sticky="w", padx=14, pady=4)

        details = ctk.CTkFrame(right, corner_radius=8)
        details.grid(row=3, column=0, sticky="nsew", padx=12, pady=(0, 10))
        details.columnconfigure(0, weight=1)
        details.rowconfigure(1, weight=1)

        ctk.CTkLabel(details, text="CustomTkinter Snippet", font=mod.HEADING4).grid(
            row=0, column=0, sticky="w", padx=14, pady=(12, 4)
        )

        self.code_text = ctk.CTkTextbox(details, wrap="none")
        self.code_text.grid(row=1, column=0, sticky="nsew", padx=14, pady=(6, 14))
        self.code_text.configure(state="disabled")

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=1, column=0, sticky="w", padx=14, pady=(0, 8))
        ctk.CTkButton(footer, text="Close", width=90, command=self.close_dialog).grid(
            row=0, column=0, sticky="w"
        )

        self.status_label = ctk.CTkLabel(self, textvariable=self.status_var, anchor="w")
        self.status_label.grid(row=2, column=0, columnspan=2, sticky="ew", padx=14, pady=(0, 10))

    def _restore_geometry(self):
        saved_geometry = pref.preference_setting(
            db_file_path=DB_FILE_PATH,
            scope="window_geometry",
            preference_name="icon_browser",
            default=DEFAULT_GEOMETRY,
        )
        self.geometry(saved_geometry)

    def _save_geometry(self):
        geometry_row = pref.new_preference_dict(
            scope="window_geometry",
            preference_name="icon_browser",
            data_type="str",
            preference_value=self.geometry(),
        )
        current_geometry_row = pref.preference_row(
            db_file_path=DB_FILE_PATH,
            scope="window_geometry",
            preference_name="icon_browser",
        )
        if current_geometry_row is not None:
            geometry_row = current_geometry_row
            geometry_row["preference_value"] = self.geometry()
        pref.upsert_preference(db_file_path=DB_FILE_PATH, preference_row_dict=geometry_row)

    def _populate_icon_buttons(self):
        self.icon_listbox.delete(0, tk.END)
        for name in self.filtered_icons:
            self.icon_listbox.insert(tk.END, name)
        self.count_label.configure(text=f"{len(self.filtered_icons)} icons")

    def _listbox_background(self):
        try:
            frame_theme = ctk.ThemeManager.theme["CTkFrame"]
            colour = frame_theme["fg_color"][cbtk.str_mode_to_int()]
            return colour
        except Exception:
            return "#ffffff"

    def _listbox_foreground(self):
        try:
            return ctk.ThemeManager.theme["CTkLabel"]["text_color"][cbtk.str_mode_to_int()]
        except Exception:
            return "#1f1f1f"

    def _listbox_selected_background(self):
        try:
            return cbtk.get_color_from_name("CTkButton", "fg_color")
        except Exception:
            return "#1f6aa5"

    def _listbox_selected_foreground(self):
        try:
            return ctk.ThemeManager.theme["CTkButton"]["text_color"][cbtk.str_mode_to_int()]
        except Exception:
            return "#ffffff"

    def _toggle_category_picker(self):
        if self.category_picker is not None and self.category_picker.winfo_exists():
            self._close_category_picker()
        else:
            self._open_category_picker()

    def _open_category_picker(self):
        if self.category_picker_button is None:
            return

        self._close_category_picker()
        self.filtered_categories = ["All categories", *self.all_categories]

        picker = ctk.CTkToplevel(self)
        picker.withdraw()
        picker.overrideredirect(True)
        picker.attributes("-topmost", True)
        picker.transient(self)
        picker.columnconfigure(0, weight=1)
        picker.rowconfigure(1, weight=1)
        picker.bind("<Escape>", self._close_category_picker)
        picker.bind("<FocusOut>", self._on_category_picker_focus_out)

        border_frame = ctk.CTkFrame(picker, corner_radius=8)
        border_frame.grid(row=0, column=0, sticky="nsew")
        border_frame.columnconfigure(0, weight=1)
        border_frame.rowconfigure(1, weight=1)

        search_entry = ctk.CTkEntry(
            border_frame,
            placeholder_text="Filter categories",
            width=260,
        )
        search_entry.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 8))
        search_entry.bind("<KeyRelease>", self._on_category_picker_search)
        search_entry.bind("<Down>", self._focus_category_listbox)

        list_frame = ctk.CTkFrame(border_frame, corner_radius=8)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        listbox = tk.Listbox(
            list_frame,
            activestyle="none",
            borderwidth=0,
            highlightthickness=0,
            relief="flat",
            exportselection=False,
            selectmode=tk.SINGLE,
            background=self._listbox_background(),
            foreground=self._listbox_foreground(),
            selectbackground=self._listbox_selected_background(),
            selectforeground=self._listbox_selected_foreground(),
            font=mod.REGULAR_TEXT,
        )
        listbox.grid(row=0, column=0, sticky="nsew")
        listbox.bind("<<ListboxSelect>>", self._on_category_picker_select)
        listbox.bind("<Double-Button-1>", self._on_category_picker_activate)
        listbox.bind("<Return>", self._on_category_picker_activate)
        listbox.bind("<Escape>", self._close_category_picker)

        scrollbar = ctk.CTkScrollbar(
            list_frame,
            orientation="vertical",
            command=listbox.yview,
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        listbox.configure(yscrollcommand=scrollbar.set)

        self.category_picker = picker
        self.category_picker_listbox = listbox
        self.category_picker_search_entry = search_entry
        self._populate_category_picker_list()
        self._position_category_picker()
        picker.deiconify()
        picker.focus_force()
        search_entry.focus_set()

    def _position_category_picker(self):
        if self.category_picker is None or self.category_picker_button is None:
            return

        self.update_idletasks()
        button_x = self.category_picker_button.winfo_rootx()
        button_y = self.category_picker_button.winfo_rooty()
        button_height = self.category_picker_button.winfo_height()
        button_width = self.category_picker_button.winfo_width()
        popup_height = 320
        self.category_picker.geometry(f"{button_width}x{popup_height}+{button_x}+{button_y + button_height + 4}")

    def _populate_category_picker_list(self):
        if self.category_picker_listbox is None:
            return

        current_category = self.category_var.get()
        self.category_picker_listbox.delete(0, tk.END)
        for category_name in self.filtered_categories:
            self.category_picker_listbox.insert(tk.END, category_name)

        if current_category in self.filtered_categories:
            index = self.filtered_categories.index(current_category)
            self.category_picker_listbox.selection_set(index)
            self.category_picker_listbox.activate(index)
            self.category_picker_listbox.see(index)
        elif self.filtered_categories:
            self.category_picker_listbox.selection_set(0)
            self.category_picker_listbox.activate(0)

    def _on_category_picker_search(self, _event=None):
        if self.category_picker_search_entry is None:
            return

        term = self.category_picker_search_entry.get().strip().lower()
        all_categories = ["All categories", *self.all_categories]
        if term:
            self.filtered_categories = [name for name in all_categories if term in name.lower()]
        else:
            self.filtered_categories = all_categories
        self._populate_category_picker_list()

    def _focus_category_listbox(self, _event=None):
        if self.category_picker_listbox is not None:
            self.category_picker_listbox.focus_set()
        return "break"

    def _on_category_picker_activate(self, _event=None):
        if self.category_picker_listbox is None:
            return "break"

        selection = self.category_picker_listbox.curselection()
        if not selection:
            return "break"

        self.category_var.set(self.filtered_categories[selection[0]])
        if self.category_picker_button is not None:
            self.category_picker_button.configure(text=f"Category: {self.category_var.get()}")
        self._close_category_picker()
        self._on_search()
        return "break"

    def _on_category_picker_select(self, _event=None):
        self._on_category_picker_activate()

    def _on_category_picker_focus_out(self, _event=None):
        if self.category_picker is None:
            return

        focused_widget = self.focus_get()
        if focused_widget is None:
            self.after(10, self._close_category_picker)
            return

        widget = focused_widget
        while widget is not None:
            if widget == self.category_picker:
                return
            widget = widget.master

        self.after(10, self._close_category_picker)

    def _close_category_picker(self, _event=None):
        if self.category_picker is not None and self.category_picker.winfo_exists():
            self.category_picker.destroy()
        self.category_picker = None
        self.category_picker_listbox = None
        self.category_picker_search_entry = None
        return "break"

    def _on_search(self, _event=None):
        self._apply_filters()

        self._populate_icon_buttons()

        if self.filtered_icons:
            self.icon_listbox.selection_clear(0, tk.END)
            self.icon_listbox.selection_set(0)
            self.icon_listbox.activate(0)
            self.icon_listbox.see(0)
            self._select_icon(self.filtered_icons[0])
        else:
            self.current_name = None
            self.selected_name_var.set("No matches")
            self._set_code_text("")
            self.preview_label.configure(image="", text="")
            self.meta_name.configure(text="")
            self.meta_fill.configure(text="")
            self.meta_size.configure(text="")
            self.status_var.set("No icons match the current search and category filters.")

    def _apply_filters(self):
        term = self.search_var.get().strip().lower()
        selected_category = self.category_var.get()

        if selected_category == "All categories":
            category_icons = self.all_icons
        else:
            category_icons = ctkfontawesome.icons_in_category(selected_category)

        if term:
            self.filtered_icons = [name for name in category_icons if term in name.lower()]
        else:
            self.filtered_icons = list(category_icons)

    def _selected_size(self) -> int:
        try:
            size = int(self.size_var.get())
        except ValueError:
            size = 96
            self.size_var.set(str(size))
        return max(16, min(size, 256))

    def _select_icon(self, name: str):
        self.current_name = name
        self.selected_name_var.set(name)
        self._refresh_icon_selection()
        self._refresh_preview()

    def _selected_hover_color(self):
        try:
            return cbtk.get_color_from_name("CTkButton", "hover_color")
        except Exception:
            return None

    def _refresh_icon_selection(self):
        if self.current_name not in self.filtered_icons:
            self.icon_listbox.selection_clear(0, tk.END)
            return
        icon_index = self.filtered_icons.index(self.current_name)
        self.icon_listbox.selection_clear(0, tk.END)
        self.icon_listbox.selection_set(icon_index)
        self.icon_listbox.activate(icon_index)
        self.icon_listbox.see(icon_index)

    def _on_listbox_select(self, _event=None):
        selection = self.icon_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        if index < len(self.filtered_icons):
            name = self.filtered_icons[index]
            if name != self.current_name:
                self._select_icon(name)

    def _refresh_preview(self, _event=None):
        if not self.current_name:
            return
        self._render_preview(self.current_name)

    def _render_preview(self, name: str):
        size = self._selected_size()
        self._set_code_text(self._build_code_snippet(name))

        try:
            image = ctkfontawesome.icon_to_ctkimage(
                name,
                fill=self.fill_var.get().strip() or None,
                scale_to_width=size,
            )
        except Exception as exc:
            self.current_image = None
            self.preview_label.configure(
                image="",
                text="Image preview unavailable\n\nInstall optional image dependencies for ctkfontawesome.",
            )
            self.status_var.set(f"{type(exc).__name__}: {exc}")
            return

        self.current_image = image
        self.preview_label.configure(image=image, text="")
        self.meta_name.configure(text=f"Name:  {name}")
        self.meta_fill.configure(text=f"Fill:  {self.fill_var.get().strip() or 'default'}")
        self.meta_size.configure(text=f"Size:  {size}px")
        self.status_var.set(f"Previewing '{name}' at {size}px.")

    def _set_code_text(self, value: str):
        self.code_text.configure(state="normal")
        self.code_text.delete("1.0", tk.END)
        self.code_text.insert("1.0", value)
        self.code_text.configure(state="disabled")

    def _copy_name(self):
        if not self.current_name:
            return
        ok, error = cbtk.clipboard_copy(self.current_name, self)
        if ok:
            self.status_var.set(f"Copied icon name '{self.current_name}'.")
        else:
            self.status_var.set("Clipboard copy is unavailable on this system.")

    def _copy_code(self):
        if not self.current_name:
            return
        code = self._build_code_snippet(self.current_name)
        ok, error = cbtk.clipboard_copy(code, self)
        if ok:
            self.status_var.set(f"Copied CustomTkinter snippet for '{self.current_name}'.")
        else:
            self.status_var.set("Clipboard copy is unavailable on this system.")

    def _build_code_snippet(self, name: str) -> str:
        fill = self.fill_var.get().strip() or "#1f6aa5"
        size = self._selected_size()
        return (
            "import customtkinter as ctk\n"
            "from ctkfontawesome import icon_to_ctkimage\n\n"
            "app = ctk.CTk()\n\n"
            f"icon = icon_to_ctkimage(\"{name}\", fill=\"{fill}\", scale_to_width={size})\n"
            "button = ctk.CTkButton(\n"
            "    app,\n"
            "    text=\"\",\n"
            "    image=icon,\n"
            "    width=44,\n"
            "    height=44,\n"
            ")\n"
            "button.pack(padx=20, pady=20)\n\n"
            "app.mainloop()\n"
        )

    def close_dialog(self, _event=None):
        self._save_geometry()
        root = self.master
        self.destroy()
        if root is not None:
            root.destroy()


def main():
    configure_browser_runtime()
    app = ctk.CTk()
    app.withdraw()
    browser = IconBrowser(master=app)
    browser.mainloop()


if __name__ == "__main__":
    main()
