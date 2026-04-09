import customtkinter as ctk
import pyperclip


class UnsupportedPlacementMethod(Exception):
    """
    A custom exception to handle unsupported/indeterminate widget placement method.
    """

    def __init__(self, message):
        self.message = message  # Store the error message

class CTkButtonDnD:
    """Facilitate drag and drop of CustomTkinter CTkButton.
    Drag a CTkButton over another CTkButton and update the drop target colours,to
    those of the dragged widget. When the operation is completed, the dragged
    widget is returned to its original position."""
    source_fg_color = ''
    source_hover_color = ''
    widget_property = ''

    def __init__(self, master, widget, enable_drag=True, enable_drop=True, paste_function=None, widget_property=None):
        self.widget = widget
        self.widget.propagate(False)
        self.master = master

        self.enable_drag = enable_drag
        self.enable_drop = enable_drop
        self.paste_function = paste_function
        self.widget_property = widget_property
        self.placement_method, self.parent_widget, self.widget_row, self.widget_column = None, None, None, None
        self.initial_position = None
        if enable_drag:
            self.placement_method, self.parent_widget, self.widget_row, self.widget_column = self.widget_info()
            widget.bind("<Button-1>", self.on_click)
            widget.bind("<ButtonRelease-1>", lambda event: self.restore_position())
            # self.widget_x_restore, self.widget_y_restore = 0, 0
            master.update_idletasks()
            self.widget_x_restore = widget.winfo_x()
            self.widget_y_restore = widget.winfo_y()
            self.pointer_start_x, self.pointer_start_y = 0, 0

        if enable_drop:
            self.widget.bind("<<Drop>>", self.drop)

        self.widget.bind("<Destroy>", self.cleanup)

    def cleanup(self, event=None):
        """Cleanup method to be called when the associated CTkButton widget is destroyed."""
        self.widget.unbind('<Destroy>')

    def on_click(self, event):
        self.pointer_start_x, self.pointer_start_y = event.x, event.y
        widget = event.widget.master

        if self.enable_drag:
            CTkButtonDnD.source_fg_color = widget.cget('fg_color')
            CTkButtonDnD.source_hover_color = widget.cget('hover_color')
            self.widget.bind("<B1-Motion>", self.drag_motion)

        if self.enable_drop:
            self.widget.bind("<ButtonRelease-1>", self.drop)

    def drag_motion(self, event):
        x = self.widget.winfo_x() + event.x - self.pointer_start_x
        y = self.widget.winfo_y() + event.y - self.pointer_start_y
        self.widget.lift()
        self.widget.place(x=x, y=y)

    def drop(self, event):
        self.widget.lower()
        widget = event.widget
        pyperclip.copy(CTkButtonDnD.source_fg_color)

        return
        # TODO: Fix this vvv
        self.paste_function(event=None, widget_property=self.widget_property,
                            property_colour=CTkButtonDnD.source_fg_color)

    def restore_position(self):

        self.widget.lower()
        x, y = self.master.winfo_pointerxy()
        target_widget = self.widget.winfo_containing(x, y)
        self.widget.configure(self.master)
        # print(f'Placement method: {self.placement_method}; widget type: {type(self.widget)}')
        if self.placement_method == 'grid':
            # print(f'Restoring {self.widget}, inside {self.master} at: {self.widget_row} : {self.widget_column}')
            self.widget.grid(row=self.widget_row, column=self.widget_column)
        else:
            self.widget.place(x=self.widget_x_restore, y=self.widget_y_restore)
        self.master.update_idletasks()
        target_widget.event_generate('<<Drop>>')

    def widget_info(self):
        def grid_details():
            try:
                info = self.widget.grid_info()
                parent = self.widget.master
                widget_row = info['row']
                widget_column = info['column']
                return parent, widget_row, widget_column
            except KeyError:
                return None, None, None

        def place_details():
            try:
                info = self.widget.place_info()
                parent = self.widget.master
                widget_x = info['x']
                widget_y = info['y']
                return parent, widget_x, widget_y
            except KeyError:
                return None, None, None

        parent_widget, row, column = grid_details()
        if parent_widget:
            return 'grid', parent_widget, row, column

        parent_widget, row, column = place_details()
        if parent_widget:
            return 'place', parent_widget, row, column

        raise UnsupportedPlacementMethod(f'Widget ({self.widget}) placement method could not be confirmed as "grid" or '
                                         f'"place".')


if __name__ == "__main__":
    def reset_colors():
        button1.configure(fg_color="red", hover_color="green")
        button2.configure(fg_color="blue", hover_color="black")


    root = ctk.CTk()

    root.geometry("310x200+200+200")

    button1 = ctk.CTkButton(root, fg_color="red", hover_color="green", width=100, height=50)
    button1.place(x=10, y=50)
    button1_dnd = CTkButtonDnD(root, button1, True, True)

    button2 = ctk.CTkButton(root, fg_color="blue", hover_color="black", width=100, height=50)
    button2.place(x=200, y=50)
    button2_dnd = CTkButtonDnD(root, button2, True, True)

    button_reset = ctk.CTkButton(root, text='Reset', width=100, command=reset_colors)
    button_reset.place(x=200, y=160)

    root.mainloop()
