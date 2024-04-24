from customtkinter import CTk, CTkToplevel
from model.ctk_theme_builder import log_call
import utils.loggerutl as log


@log_call
def position_child_widget(parent_widget: CTk, child_widget: CTkToplevel, y_offset=0.5, x_offset=0.45):
    """
    Centers a child CTkToplevel widget within its parent CTk or CTkToplevel widget.

    Args:
        parent_widget: The parent CTk or CTkToplevel widget.
        child_widget: The child CTkToplevel widget to be centered.
        x_offset: Offset from the parent's x position
        y_offset: Offset from the parent's y position
    """
    parent_widget.update_idletasks()
    parent_width = parent_widget.winfo_width()
    parent_height = parent_widget.winfo_height()
    child_width = child_widget.winfo_width()
    child_height = child_widget.winfo_height()

    if parent_widget is None:
        position_x = int((child_widget.winfo_screenwidth() - child_width) / 2)
        position_y = int((child_widget.winfo_screenheight() - child_height) / 2)
    else:
        position_x = int(parent_width * x_offset + parent_widget.winfo_x() - .5 * child_width)
        position_y = int(parent_height * y_offset + parent_widget.winfo_y() - .5 * child_height)

    child_width = child_widget.winfo_width()
    child_height = child_widget.winfo_height()

    # Set geometry with format "WidthxHeight+Xoffset+Yoffset"
    geometry = f"{child_width}x{child_height}+{position_x}+{position_y}"
    log.log_debug(f"Parent position x: {position_x}")
    log.log_debug(f"Parent position y: {position_y}")
    log.log_debug(f"Child geometry: {geometry}")

    child_widget.geometry(geometry)
    parent_widget.update_idletasks()
    child_widget.lift()

@log_call
def offset_widget(parent_widget: CTk, y_offset, x_offset):
    """
    Create offset coordinates, based on parent widget.

    Args:
        parent_widget: The parent CTk or CTkToplevel widget.
        x_offset: Offset from the parent's x position
        y_offset: Offset from the parent's y position
    """
    parent_widget.update_idletasks()
    parent_width = parent_widget.winfo_width()
    parent_height = parent_widget.winfo_height()

    position_x = int(parent_width * x_offset + parent_widget.winfo_x())
    position_y = int(parent_height * y_offset + parent_widget.winfo_y())




if __name__ == "__main__":
    # Example usage
    parent_window = CTk()
    parent_window.geometry("500x500")
    child_window = CTkToplevel(parent_window)
    child_window.geometry("250x100")

    # Add some content to the child window (optional)
    child_window.title("This child is centered!")

    centre_child_widget(parent_window, child_window)

    parent_window.mainloop()

