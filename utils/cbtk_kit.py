__title__ = 'CB CustomTkinter Toolkit'
__author__ = 'Clive Bostock'
__version__ = "1.0.0"
__license__ = 'MIT - see LICENSE.md'

import tkinter as tk
import customtkinter as ctk
from customtkinter import ThemeManager
from PIL import Image
import textwrap
import json
from matplotlib.colors import is_color_like
import utils.color_constants as color_constants

# Constants
# These aren't true sizes as per WEB design
HEADING1 = ('Roboto', 26)
HEADING2 = ('Roboto', 22)
HEADING3 = ('Roboto', 20)
HEADING4 = ('Roboto', 18)
HEADING5 = ('Roboto', 16)
# HEADING_UL = 'Roboto 11 underline'
REGULAR_TEXT = ('Roboto', 13)

SMALL_TEXT = ('Roboto', 8)
TOOLTIP_DELAY = 1


def hex2rgb(hex_color: str) -> tuple:
    return tuple(int(hex_color.strip("#")[i:i + 2], 16) for i in (0, 2, 4))


def rgb2hex(rgb_color: tuple) -> str:
    return "#{:02x}{:02x}{:02x}".format(round(rgb_color[0]), round(rgb_color[1]), round(rgb_color[2]))


def contrast_colour(color: str, differential: int = 20):
    """The contrast_colour function, accepts a hex colour code (format #RRGGBB) and generates a slightly contrasting
    colour, based upon the specified increment. The larger the increment, the bigger the deviation from the original
    colour."""
    if color is None:
        # This occurs where we have a colour property set to "transparent", these render as white
        # so return a grey as a contrast.
        return '#b0b0b0'
    if not str(color).startswith("#"):
        convert_hex = color_constants.colors[color].hex_format()
        color_rgb = hex2rgb(convert_hex)
    else:
        color_rgb = hex2rgb(color)

    if color_rgb[0] > differential:
        rgb_0 = color_rgb[0] - differential
    else:
        rgb_0 = color_rgb[0] + differential

    if color_rgb[1] > differential:
        rgb_1 = color_rgb[1] - differential
    else:
        rgb_1 = color_rgb[1] + differential

    if color_rgb[2] > differential:
        rgb_2 = color_rgb[2] - differential
    else:
        rgb_2 = color_rgb[2] + differential

    return rgb2hex((rgb_0, rgb_1, rgb_2))


def shade_up(color: str, differential: int = 20, multiplier: int = 1):
    """The shade_up function, accepts a hex colour code (format #RRGGBB) and generates a lighter shade of
    the colour, based upon the specified differential and an optional multiplier. The larger the increment,
    the bigger the deviation from the original colour."""
    compound_differential = differential * multiplier
    if color is None:
        # This occurs where we have a colour property set to "transparent", these render as white
        # so return a grey as a contrast.
        return '#b0b0b0'
    if not str(color).startswith("#"):
        convert_hex = color_constants.colors[color].hex_format()
        color_rgb = hex2rgb(convert_hex)
    else:
        color_rgb = hex2rgb(color)

    if color_rgb[0] + compound_differential > 255 or color_rgb[1] + compound_differential > 255 \
            or color_rgb[2] + compound_differential > 255:
        # Don't perturb the colour balance
        return color

    rgb_0 = color_rgb[0] + compound_differential
    rgb_1 = color_rgb[1] + compound_differential
    rgb_2 = color_rgb[2] + compound_differential

    return rgb2hex((rgb_0, rgb_1, rgb_2))


def shade_down(color: str, differential: int = 20, multiplier: int = 1):
    """The shade_down function, accepts a hex colour code (format #RRGGBB) and generates a darker shade of
    the colour, based upon the specified differential and an optional multiplier. The larger the increment,
    the bigger the deviation from the original colour."""
    compound_differential = differential * multiplier
    if color is None:
        # This occurs where we have a colour property set to "transparent", these render as white
        # so return a grey as a contrast.
        return '#b0b0b0'
    if not str(color).startswith("#"):
        convert_hex = color_constants.colors[color].hex_format()
        color_rgb = hex2rgb(convert_hex)
    else:
        color_rgb = hex2rgb(color)

    if color_rgb[0] - compound_differential < 0 or color_rgb[1] - compound_differential < 0 \
            or color_rgb[2] - compound_differential < 0:
        # Don't perturb the colour balance
        return color

    rgb_0 = color_rgb[0] - compound_differential
    rgb_1 = color_rgb[1] - compound_differential
    rgb_2 = color_rgb[2] - compound_differential

    return rgb2hex((rgb_0, rgb_1, rgb_2))


def get_color_from_name(widget_type: str, widget_property: str = "fg_color"):
    """Gets the colour code associated with the supplied widget property,
    as defined by the currently active CustomTkinter theme."""
    mode = ctk.get_appearance_mode()
    if mode == 'Light':
        mode_idx = 0
    else:
        mode_idx = 1
    colour = ThemeManager.theme[widget_type][widget_property][mode_idx]
    return colour


def geometry_offset(window_geometry, x_increment=0, y_increment=0):
    """The geometry_offset function, receives a fully qualified tkinter geometry and returns the screen position
    components. You can also supply additional offsets (x_increment, y_increment) to be used to increment the
    returned value. This function thus allows you to base a window position, based on another window's position:

    an_other_window_geometry = retrieved_geometry
    offset = cbtk_kit.geometry_offset(an_other_window_geometry, 30, 50)
    top_level.geometry(f"300x400{offset}")
    """
    if window_geometry is None or not window_geometry:
        return '+0+0'

    # There are situations where Tk returns a '+-' within the geometry string.
    if '-' in window_geometry.replace('+-', '+'):
        print("WARNING: cbtk_kit.geometry_offset(), does not support negative offsets!")
        return "+0+0"

    geometry_components = window_geometry.replace('+-', '+').split('+')
    geometry_x = geometry_components[1]
    geometry_x = int(geometry_x) + x_increment
    geometry_y = geometry_components[2]
    geometry_y = int(geometry_y) + y_increment
    return f"+{geometry_x}+{geometry_y}"


def str_mode_to_int(mode=None):
    """Returns the integer representing the CustomTkinter theme appearance mode, 0 for "Light", 1 for "Dark". If
    "Dark" or "Light" is not passed as a parameter, the current theme mode is detected and the return value is based
    upon that. """
    if mode is not None:
        appearance_mode = mode
    else:
        appearance_mode = ctk.get_appearance_mode()
    if appearance_mode.lower() == "light":
        return 0
    return 1


def load_image(light_image, dark_image=None, image_size: tuple = (30, 30)):
    """ load rectangular image with path relative to PATH """

    if dark_image is None:
        dark_image = light_image

    return ctk.CTkImage(light_image=Image.open(light_image),
                        dark_image=Image.open(dark_image),
                        size=image_size)
    # return ImageTk.PhotoImage(Image.open(path).resize((image_size, image_size)))


def theme_property_color(theme_file_path, widget_type: str, widget_property: str, mode: str):
    """Based on the pathname to the CustomTkinter theme's JSON file, we return the colour code, for the specified
    CustomTkinter appearance mode, and widget property. """
    with open(theme_file_path) as json_file:
        theme_dict = json.load(json_file)

    mode_idx = 0 if mode.lower() == 'light' else 1
    property_colour = theme_dict[widget_type][widget_property][mode_idx]
    return property_colour


def theme_property(theme_file_path, widget_type: str, widget_property: str):
    """Based on the pathname to the CustomTkinter theme's JSON file, we return the property value, for the specified
    CustomTkinter widget property. """
    with open(theme_file_path) as json_file:
        theme_dict = json.load(json_file)

    property_colour = theme_dict[widget_type][widget_property]
    return property_colour


def theme_provenence_attribute(theme_file_path, attribute: str, value_on_missing: str = 'Unknown'):
    """Based on the pathname to the CustomTkinter theme's JSON file, we return the requested provenance value
    associated with the supplied attribute."""
    with open(theme_file_path) as json_file:
        theme_dict = json.load(json_file)
    try:
        property_colour = theme_dict["provenance"][attribute]
    except KeyError:
        return value_on_missing
    return property_colour


def wrap_string(text_string: str, wrap_width=80):
    """Function which takes a string of text and wraps it, at word boundaries, based on a specified width.
    :rtype@ str
    :param@ text_string:
    :param@ wrap_width:
    """
    wrapper = textwrap.TextWrapper(width=wrap_width)
    word_list = wrapper.wrap(text=text_string)
    string = ''
    for element in word_list:
        string = string + element + '\n'
    return string


class CBtkMenu(tk.Menu):
    widget_registry = []

    def __init__(self,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)

        mode = ctk.get_appearance_mode()
        if mode == 'Light':
            mode = 0
        else:
            mode = 1
        fg_color = ThemeManager.theme["DropdownMenu"]["fg_color"][mode]
        hover_color = ThemeManager.theme["DropdownMenu"]["hover_color"][mode]
        text_color = ThemeManager.theme["DropdownMenu"]["text_color"][mode]

        platform_font = ThemeManager.theme["CTkFont"]
        self._font_family = platform_font["family"]
        self._font_size = 11
        self._font_weight = platform_font["weight"]

        self.configure(bg=fg_color,
                       fg=text_color,
                       activebackground=hover_color,
                       activeforeground=text_color,
                       font=(self._font_family, self._font_size, self._font_weight))

        CBtkMenu.widget_registry.append(self)

    @classmethod
    def update_widgets_mode(cls):
        """Method to update all menu widgets following an appearance mode change."""
        for widget in CBtkMenu.widget_registry:
            try:
                widget.update_appearance_mode()
            except tk.TclError:
                # print(f'Skipping widget configuration')
                pass

    def update_appearance_mode(self):
        """Method called to scan through rendered widgets and update to a new appearance mode setting."""
        mode = ctk.get_appearance_mode()
        if mode == 'Light':
            mode = 0
        else:
            mode = 1

        fg_color = ThemeManager.theme["DropdownMenu"]["fg_color"][mode]
        hover_color = ThemeManager.theme["DropdownMenu"]["hover_color"][mode]
        text_color = ThemeManager.theme["DropdownMenu"]["text_color"][mode]

        self.configure(bg=fg_color,
                       fg=text_color,
                       activebackground=hover_color,
                       activeforeground=text_color)


class InvalidParameterValue(Exception):
    """Unexpected parameter value passed to a function."""
    pass


def valid_colour(colour):
    """Accept a color name / hex code and validate it, returning boolean True, if the colour is valid and False if it
    is invalid.
    :param colour:
    :return: bool"""
    return is_color_like(colour)


class CBtkMessageBox(object):
    """Message box class for CustomTkinter. Up to 4 buttons are rendered where their respective buttonN_text
    parameter has a value. An integer value us returned, dependant upon the respective button number, of the button
    pressed. """

    def __init__(self, title='CBtkMessageBox',
                 message='',
                 button_height=2,
                 button1_text='OK',
                 button2_text='',
                 button3_text='',
                 button4_text='',
                 master=None,
                 geometry=None):
        """
        :param title:
        :param message:
        :param button_height:
        :param button1_text:
        :param button2_text:
        :param button3_text:
        :param button4_text:
        """
        self.master = master
        button_width = 100
        self.message = wrap_string(text_string=message, wrap_width=40)  # Is message to display
        self.button1_text = button1_text  # Button 1 (outputs '1')
        self.button2_text = button2_text  # Button 2 (outputs '2')
        self.button3_text = button3_text  # Button 3 (outputs '3')
        self.button4_text = button4_text  # Button 4 (outputs '4')
        self.choice = ''  # it will be the return of messagebox according to button press

        # Create TopLevel dialog for the messagebox
        self.root = ctk.CTkToplevel()
        self.root.title(title)

        self.frm_main = ctk.CTkFrame(master=self.root)
        self.frm_main.pack(fill=tk.BOTH)
        self.frm_main.configure(corner_radius=0)
        # self.frm_main.columnconfigure(0, weight=1)
        # self.root.rowconfigure(0, weight=1)
        # self.frm_main.rowconfigure(0, weight=1)

        self.frm_message = ctk.CTkFrame(master=self.frm_main)
        self.frm_message.pack(expand=True, fill=tk.BOTH)
        self.frm_message.configure(corner_radius=0)

        self.frm_buttons = ctk.CTkFrame(master=self.frm_main, corner_radius=0)
        self.frm_buttons.pack(side=tk.BOTTOM, fill=tk.X, ipady=20)
        self.frm_buttons.configure(corner_radius=0)
        # self.frm_main.rowconfigure(1, weight=0)

        # Creating Label For message
        self.lbl_message = ctk.CTkLabel(self.frm_message, text=self.message)
        self.lbl_message.pack(fill=tk.BOTH, padx=10, pady=(20, 10))

        button_count = 1
        if button2_text:
            button_count += 1
        if button3_text:
            button_count += 1
        if button4_text:
            button_count += 1

        # Setting Geometry
        if self.master:
            try:
                master.attributes('-disabled', 1)
            except AttributeError:
                pass
            # Added for MacOS:
            except tk.TclError:
                pass

            try:
                self.root.geometry(master.geometry())
            except AttributeError:
                pass
            # Added for MacOS:
            except tk.TclError:
                pass

        if button_count == 1:
            pad_x = 50
            self.root.geometry("320x155")
        elif button_count == 2:
            pad_x = 30
            self.root.geometry("320x155")
        elif button_count == 3:
            pad_x = 20
            self.root.geometry("420x155")
        else:
            self.root.geometry("440x155")
            pad_x = 5
        # Override if the API has been instructed to do so...
        if geometry:
            self.root.geometry(geometry)

        pad_y = (10, 0)

        # Create a button, corresponding to button1_text
        self.button1_text = ctk.CTkButton(self.frm_buttons,
                                          text=self.button1_text,
                                          command=self.click1,
                                          width=button_width,
                                          height=button_height)
        if button_count == 1:
            self.button1_text.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        else:
            self.button1_text.grid(row=0, column=0, padx=pad_x, pady=pad_y)

        # Create a button, corresponding to  button1_text
        # self.button1_text.info = self.button1_text.place_info()

        # Create a button, corresponding to  button2_text
        if button2_text:
            self.button2_text = ctk.CTkButton(self.frm_buttons,
                                              text=self.button2_text,
                                              command=self.click2,
                                              width=button_width,
                                              height=button_height)
            self.button2_text.grid(row=0, column=1, padx=pad_x, pady=pad_y)
        # Create a button, corresponding to  button3_text
        if button3_text:
            self.button3_text = ctk.CTkButton(self.frm_buttons,
                                              text=self.button3_text,
                                              command=self.click3,
                                              width=button_width,
                                              height=button_height)
            self.button3_text.grid(row=0, column=2, padx=pad_x, pady=pad_y)
        # Create a button, corresponding to button4_text
        if button4_text:
            self.button4_text = ctk.CTkButton(self.frm_buttons,
                                              text=self.button4_text,
                                              command=self.click4,
                                              width=button_width,
                                              height=button_height)
            self.button4_text.grid(row=0, column=3, padx=pad_x, pady=pad_y)

        # Make the message box visible
        self.frm_main.update_idletasks()
        self.root.grab_set()

        try:
            self.master.wait_window(self.root)
        except AttributeError:
            pass
        except tk.TclError:
            pass

    # Function on Closing MessageBox
    def closed(self):
        self.root.destroy()  # Destroying Dialogue
        self.choice = 'closed'  # Assigning Value
        if self.master:
            try:
                self.master.attributes('-disabled', 0)
            except AttributeError:
                pass
            # Added for MacOS:
            except tk.TclError:
                pass
            try:
                self.master.lift()
            except AttributeError:
                pass
            # Added for MacOS:
            except tk.TclError:
                pass

    # Function on pressing button1_text
    def click1(self):
        self.root.destroy()  # Destroying Dialogue
        self.choice = 1  # Assigning Value
        if self.master:
            try:
                self.master.attributes('-disabled', 0)
            except AttributeError:
                pass
            # Added for MacOS:
            except tk.TclError:
                pass
            try:
                self.master.lift()
            except AttributeError:
                pass
            # Added for MacOS:
            except tk.TclError:
                pass

    # Function on pressing button2_text
    def click2(self):
        self.root.destroy()  # Destroying Dialogue
        self.choice = 2  # Assigning Value
        if self.master:
            try:
                self.master.attributes('-disabled', 0)
            except AttributeError:
                pass
            # Added for MacOS:
            except tk.TclError:
                pass
            try:
                self.master.lift()
            except AttributeError:
                pass
            # Added for MacOS:
            except tk.TclError:
                pass

    # Function on pressing button3_text
    def click3(self):
        self.root.destroy()  # Destroying Dialogue
        self.choice = 3  # Assigning Value
        if self.master:
            try:
                self.master.attributes('-disabled', 0)
            except AttributeError:
                pass
            # Added for MacOS:
            except tk.TclError:
                pass
            try:
                self.master.lift()
            except AttributeError:
                pass
            # Added for MacOS:
            except tk.TclError:
                pass

    # Function on pressing button4_text
    def click4(self):
        self.root.destroy()  # Destroying Dialogue
        self.choice = 4  # Assigning Value
        if self.master:
            try:
                self.master.attributes('-disabled', 0)
            except AttributeError:
                pass
            except tk.TclError:
                pass
            try:
                self.master.lift()
            except AttributeError:
                pass
            except tk.TclError:
                pass


def raise_tk_window(window_widget: tk.Toplevel):
    """Brings a window widget to the front (above other windows), but does not lock it there."""

    try:
        window_widget.attributes('-topmost', 1)
    except AttributeError:
        pass
    # Added for MacOS:
    except tk.TclError:
        pass

    try:
        window_widget.attributes('-topmost', 0)
    except AttributeError:
        pass
    # Added for MacOS:
    except tk.TclError:
        pass


class CBtkStatusBar(tk.Entry):
    """Create a status bar on the parent window.
    Messages can be written to the status bar using the set_status_text method.

    The status_text_life can be used to auto-erase the status text after the specified number of seconds. The
    default value is 20. A value of 0 disables the auto-erase feature.

    The background and text colours, default to frame_high and text as per CustomTkinter themes. These can be overridden
    using the bg_color and fg_color parameters, respectively.

    The default value for bg_color, is derived  as the "frame_low" colour property, from the active CustomTkinter theme.

    The default value for fg_color, is derived  as the "text" colour property, from the active CustomTkinter theme

    The class has a dependency on ThemeManager from the CustomTkinter package.

    When implementing in a non-root window (TopLevel), you should call the cancel_message_timer method,
    just prior to destroying the window.
    Example:

        def on_close_client_tools(self):
            try:
                self.client_tool_status_bar.cancel_message_timer()
            except ValueError:
                # We get a value error if we haven't issued a message and incurred an "after",
                # since there is no "after" event to cancel.
                pass
            self.top_client_tool.destroy()

    """

    def __init__(self,
                 master,
                 status_text_life=30,
                 use_grid=True,
                 fg_color=None,
                 text_color=None):
        """
        :param master: Master widget, to which to attach the status bar.
        :param status_text_life: Defines, in seconds, the default longevity of messages displayed to the status bar.
        :param use_grid: Set to true if using grid method (default). If specified as False, the pack method is used.
        :param fg_color: Hex colour code (#RRGGBB), defining the background colour of the status bar.
        :param text_color: Hex colour code (#RRGGBB), defining the text colour of the status bar.
        """
        super().__init__()

        if fg_color is None:
            fg_color = self.get_color_from_name(widget_type='CTkFrame', widget_property='fg_color')
        if text_color is None:
            text_color = self.get_color_from_name(widget_type='CTkLabel', widget_property='text_color')

        self._message_id = None
        self._master = master
        self._master.update_idletasks()
        grid_size = master.grid_size()
        grid_columns = grid_size[0]
        if grid_columns == 0:
            grid_columns = 1
        grid_rows = grid_size[1]
        if grid_rows == 0:
            grid_rows = 1
        self._master.update_idletasks()
        self._app_width = self._master.winfo_width()
        self._status_text_life = status_text_life
        assert isinstance(self._status_text_life, int)

        # TODO: Uncomment relief when fixed in CTkLabel
        self.widget = ctk.CTkLabel(master,
                                   # relief=tk.SUNKEN,
                                   text='',
                                   anchor='w')
        if text_color is not None:
            self.widget.configure(text_color=text_color)

        if fg_color is not None:
            self.widget.configure(fg_color=fg_color)

        if use_grid:
            self.widget.grid(row=grid_rows + 1, column=0, padx=0, pady=0, columnspan=grid_columns, sticky='ew')
        else:
            self.widget.pack(fill="both", expand=0)

        self._orig_app_width = self._master.winfo_width()

    def auto_size_status_bar(self, event):
        # self._master.update_idletasks()
        self._app_width = self._master.winfo_width()
        if self._app_width > self._orig_app_width:
            self.widget.configure(width=self._app_width)
            self._master.update_idletasks()

    def clear_status(self):
        self.set_status_text(status_text=' ')

    @staticmethod
    def get_color_from_name(widget_type: str, widget_property="fg_color"):
        """Gets the colour code associated with the supplied widget property,
        as defined by the currently active CustomTkinter theme."""
        mode = ctk.get_appearance_mode()
        if mode == 'Light':
            mode = 0
        else:
            mode = 1
        colour = ThemeManager.theme[widget_type][widget_property][mode]
        return colour

    def set_status_text(self, status_text: str,
                        status_text_life=None):
        try:
            self.widget.configure(text='  ' + status_text)
        except tk.TclError:
            return
        if status_text_life is not None:
            message_life = status_text_life
        elif self._status_text_life:
            message_life = self._status_text_life
        else:
            message_life = 0
        if self._status_text_life:
            self._message_id = self.after(message_life * 1000, self.clear_status)

    def set_fg_color(self, fg_color):
        """The fg_color is the colour of the label component of the widget (i.e. surrounding the text)
        See customtkinter.TkLabel()"""
        self.widget.configure(fg_color=fg_color)

    def set_bg_color(self, bg_color):
        """The bg_color is the background colour of the label component. See customtkinter.CTkLabel()"""
        self.widget.configure(fg_color=bg_color)

    def set_text_color(self, text_color):
        self.widget.configure(text_color=text_color)

    def update_text_colour(self):
        """This method can be called if you flip the appearance mode between "Light" and "Dark". It interrogates the
        theme, setting the text to the colour defined by the appearance mode."""
        text_color = self.get_color_from_name(widget_type='CTkLabel', widget_property='text_color')
        self.widget.configure(text_color=text_color)

    def cancel_message_timer(self):
        """If using the status message timeout feature, it is important to use the cancel_message_timer function,
        immediately prior to closing the window, where the Window is a CTkTopLevel object. This prevents a later
        reference and consequential exception, associated with an "after" method resource reference to an object which
        is destroyed. """
        if hasattr(self, '_message_id'):
            self.after_cancel(id=self._message_id)

    @staticmethod
    def _get_property_by_name(prop_name: str):
        return ThemeManager.theme[prop_name]

    def set_status_text_life(self, status_text_life):
        self._status_text_life = status_text_life


class CBtkToolTip(object):
    """
    Create a tooltip for a given widget. By default, CustomTkinter theme colours are used for the background and text.
    You must import ThemeManager from CustomTkinter for this widget.

     The default value for bg_color, is derived  as the "frame_low" colour property, from the active
     CustomTkinter theme.

     The default value for fg_color, is derived  as the "text" colour property, from the active CustomTkinter theme

    This is customised fpr CustomTkinter, but based on a Tkinter solution found here:
    https://stackoverflow.com/questions/3221956/how-do-i-display-tooltips-in-tkinter
    """

    def __init__(self, widget, text='widget info', bg_color=None, fg_color=None):
        """
        Class initialisation.

        :param widget: The widget object to assign the tooltip to.
        :param text: The text to be displayed as the tooltip.
        :param bg_color:  Hex colour code (#RRGGBB), defining the background colour of the tooltip.
        :param fg_color:  Hex colour code (#RRGGBB), defining the text colour of the tooltip. 
        """
        if bg_color is None:
            self._bg_colour = self.get_color_from_name(widget_type='CTkToplevel', widget_property='fg_color')
        else:
            self._bg_colour = bg_color

        if fg_color is None:
            self._fg_color = self.get_color_from_name(widget_type='CTkLabel', widget_property='text_color')
        else:
            self._fg_color = fg_color

        self._wait_time = 400  # milli-seconds
        self._wrap_length = 300  # pixels
        self._widget = widget
        self._text = text
        self._widget.bind("<Enter>", self.on_enter)
        self._widget.bind("<Leave>", self.on_leave)
        self._widget.bind("<ButtonPress>", self.on_leave)
        self._id = None
        self._tw = None

    def on_enter(self, event=None):
        self._schedule()

    def on_leave(self, event=None):
        self._unschedule()
        self.hide_tooltip()

    def _schedule(self):
        self._unschedule()
        self._id = self._widget.after(self._wait_time, self.show_tooltip)

    def _unschedule(self):
        _id = self._id
        self._id = None
        if _id:
            self._widget.after_cancel(_id)

    def show_tooltip(self, event=None):
        x, y, cx, cy = self._widget.bbox("insert")
        x += self._widget.winfo_rootx() + 40
        y += self._widget.winfo_rooty() + 20
        # creates a toplevel window
        self._tw = tk.Toplevel(self._widget)
        # Leaves only the label and removes the app window
        self._tw.wm_overrideredirect(True)
        self._tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self._tw, text=self._text, justify='left', fg=self._fg_color,
                         bg=self._bg_colour, relief='solid', borderwidth=1,
                         wraplength=self._wrap_length)
        label.pack(ipadx=1)

    def hide_tooltip(self):
        tw = self._tw
        self._tw = None
        if tw:
            tw.destroy()

    @staticmethod
    def get_color_from_name(widget_type: str, widget_property: str):
        """Gets the colour code associated with the supplied widget property,
        as defined by the currently active CustomTkinter theme."""
        mode = ctk.get_appearance_mode()
        if mode == 'Light':
            mode = 0
        else:
            mode = 1
        colour = ThemeManager.theme[widget_type][widget_property][mode]
        return colour
