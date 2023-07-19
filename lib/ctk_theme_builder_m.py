__title__ = 'CB CustomTkinter Theme Builder Module'
__author__ = 'Clive Bostock'
__version__ = "1.0.0"
__license__ = 'MIT - see LICENSE.md'

import copy
import time
from pathlib import Path
import json
import customtkinter as ctk
import sqlite3
import os
from datetime import datetime

# Constants
APP_HOME = os.path.dirname(os.path.realpath(__file__))
APP_HOME = Path(os.path.dirname(APP_HOME))
CTK_SITE_PACKAGES = Path(ctk.__file__)
CTK_SITE_PACKAGES = os.path.dirname(CTK_SITE_PACKAGES)
CTK_ASSETS = CTK_SITE_PACKAGES / Path('assets')
CTK_THEMES = CTK_ASSETS / 'themes'

ASSETS_DIR = APP_HOME / 'assets'
CONFIG_DIR = ASSETS_DIR / 'config'
ETC_DIR = ASSETS_DIR / 'etc'
TEMP_DIR = APP_HOME / 'tmp'
VIEWS_DIR = ASSETS_DIR / 'views'
APP_THEMES_DIR = ASSETS_DIR / 'themes'
APP_DATA_DIR = ASSETS_DIR / 'data'
DB_FILE_PATH = APP_DATA_DIR / 'ctk_theme_builder.db'
APP_IMAGES = ASSETS_DIR / 'images'
QA_STOP_FILE = ETC_DIR / 'qa_application.stop'
QA_STARTED_FILE = ETC_DIR / 'qa_application.started'

SERVER = '127.0.0.1'

# These aren't true sizes as per WEB design
HEADING1 = ('Roboto', 26)
HEADING2 = ('Roboto', 22)
HEADING3 = ('Roboto', 20)
HEADING4 = ('Roboto', 18)
HEADING5 = ('Roboto', 16)

CTK_VERSION = ctk.__version__

# HEADING_UL = 'Roboto 11 underline'
REGULAR_TEXT = ('Roboto', 12)
SMALL_TEXT = ('Roboto', 10)
TOOLTIP_DELAY = 1

DEFAULT_VIEW = 'Basic'

SUPPORTED_WIDGETS = ["CTk",
                     "CTkButton",
                     "CTkCheckBox",
                     "CTkComboBox",
                     "CTkEntry",
                     "CTkFrame",
                     "CTkLabel",
                     "CTkOptionMenu",
                     "CTkProgressBar",
                     "CTkRadioButton",
                     "CTkScrollableFrame",
                     "CTkScrollbar",
                     "CTkSegmentedButton",
                     "CTkSlider",
                     "CTkSwitch",
                     "CTkTextbox",
                     "CTkTabview",
                     "CTkToplevel",
                     "DropdownMenu"]

COLOUR_PROPERTIES = ["border_color",
                     "button_color",
                     "button_hover_color",
                     "checkmark_color",
                     "fg_color",
                     "fg_color",
                     "hover_color",
                     "label_fg_color",
                     "placeholder_text_color",
                     "progress_color",
                     "scrollbar_button_color",
                     "scrollbar_button_hover_color",
                     "selected_color",
                     "selected_hover_color",
                     "text_color",
                     "text_color_disabled",
                     "top_fg_color",
                     "unselected_color",
                     "unselected_hover_color"]

RENDERED_PREVIEW_WIDGETS = {"CTk": [],
                            "CTkButton": [],
                            "CTkCheckBox": [],
                            "CTkComboBox": [],
                            "CTk": [],
                            "CTkDropdownMenu": [],
                            "CTkEntry": [],
                            "CTkFrame": [],
                            "frame_base": [],
                            "frame_top": [],
                            "CTkLabel": [],
                            "CTkOptionMenu": [],
                            "CTkProgressBar": [],
                            "CTkRadioButton": [],
                            "CTkScrollableFrame": [],
                            "CTkScrollbar": [],
                            "CTkSegmentedButton": [],
                            "CTkTabview": [],
                            "CTkSlider": [],
                            "CTkSwitch": [],
                            "CTkTextbox": [],
                            "CTkToplevel": []}

db_file_found = None


def app_themes_list():
    """This method generates a list of theme names, based on the json files found in the application themes folder.
     These are for use by the control panel, and can be selected in the applications preferences.
     They comprise the base-names of the theme files, with the .json extension stripped out."""
    json_files = list(APP_THEMES_DIR.glob('*.json'))
    theme_names = []
    for file in json_files:
        file = os.path.basename(file)
        theme_name = os.path.splitext(file)[0]
        theme_names.append(theme_name)
    theme_names.sort()
    return theme_names


def close_qa_app_requested():
    """Used to determine whether the QA application has been requested to close."""
    if QA_STOP_FILE.exists():
        return True
    else:
        return False


def complete_qa_stop():
    time.sleep(0.5)
    remove_qa_status_files()


def remove_qa_status_files():
    if QA_STOP_FILE.exists():
        try:
            os.remove(QA_STOP_FILE)
        except FileNotFoundError:
            pass
    if QA_STARTED_FILE.exists():
        try:
            os.remove(QA_STARTED_FILE)
        except FileNotFoundError:
            pass


def qa_app_started():
    # current dateTime
    now = datetime.now()
    # convert to string
    date_started = now.strftime("%b %d %Y %H:%M:%S")
    # Ensure we don't have a stop file lying around
    if QA_STOP_FILE.exists():
        try:
            os.remove(QA_STOP_FILE)
        except FileNotFoundError:
            pass
    with open(QA_STARTED_FILE, 'w') as f:
        pid = os.getpid()
        f.write(f'[{pid}] CTk Theme Builder QA app started at: {date_started}')


def request_close_qa_app():
    # current dateTime
    now = datetime.now()
    # convert to string
    date_started = now.strftime("%b %d %Y %H:%M:%S")
    with open(QA_STOP_FILE, 'w') as f:
        pid = os.getpid()
        f.write(f'[{pid}] CTk Theme Builder QA app close requested at: {date_started}')


def user_themes_list():
    """This method generates a list of theme names, based on the json files found in the user's themes folder
    (i.e. self.theme_json_dir). These are basically the theme file names, with the .json extension stripped out."""
    user_themes_dir = preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                         preference_name='theme_json_dir')
    json_files = list(user_themes_dir.glob('*.json'))
    theme_names = []
    for file in json_files:
        file = os.path.basename(file)
        theme_name = os.path.splitext(file)[0]
        theme_names.append(theme_name)
    theme_names.sort()
    return theme_names


def db_file_exists(db_file_path: Path):
    global db_file_found
    if db_file_found is None:
        if db_file_path.exists():
            db_file_found = True
        else:
            db_file_found = False
    return db_file_found


def patch_theme(theme_json: dict):
    """The patch_theme function, checks for incorrect theme properties. These were fixed in CustomTkinter 5.2.0.
    However, the fix in CustomTkinter included an allowance for the older, wrong names. We correct the older property
    names here."""
    if 'CTkCheckbox' in theme_json or 'CTkRadiobutton' in theme_json:
        _theme_json = copy.deepcopy(theme_json)
    else:
        return theme_json
    if 'CTkCheckbox' in _theme_json:
        _theme_json['CTkCheckBox'] = _theme_json.pop('CTkCheckbox')

    if 'CTkRadiobutton' in _theme_json:
        _theme_json['CTkRadioButton'] = _theme_json.pop('CTkRadiobutton')

    return _theme_json


def keys_exist(element, *keys):
    '''
    Check if *keys (nested) exists in `element` (dict).
    @param element:
    @param keys:
    @return Bool:
    '''
    if not isinstance(element, dict):
        raise AttributeError('keys_exists() expects dict as first argument.')
    if len(keys) == 0:
        raise AttributeError('keys_exists() expects at least two arguments, one given.')

    _element = element
    for _key in keys:
        try:
            _element = _element[_key]
        except KeyError:
            return False
    return True


def cascade_dict(palette_id: int) -> dict:
    """The cascade_dict function, extracts all the colour_cascade_properties entries, for a specified palette_id. Each
    dictionary entry represents a row from the colour_cascade_properties table.

    :param palette_id: Palette# of a displayed colour palette
    :return list: List of cascade_dict dictionaries.
    """
    if not db_file_exists(db_file_path=DB_FILE_PATH):
        print(f'Unable to locate database file located at {DB_FILE_PATH}')
        raise FileNotFoundError

    db_conn = sqlite3.connect(DB_FILE_PATH)
    db_conn.row_factory = sqlite_dict_factory
    cur = db_conn.cursor()
    cur.execute("select widget_type, widget_property "
                "from colour_cascade_properties "
                "where entry_id = :entry_id", {"entry_id": palette_id})
    _cascade_dict = cur.fetchall()
    db_conn.close()
    return _cascade_dict


def cascade_display_string(palette_id: int) -> str:
    """The cascade_list function, extracts all the colour_cascade_properties entries, for a specified palette_id. Each
     entry represents a widget/property from the colour_cascade_properties table.

    :param palette_id: Palette# of a displayed colour palette
    :return list: List of cascade_dict dictionaries.
    """

    _cascade_dict = cascade_dict(palette_id=palette_id)
    _properties_string = ''
    for record in _cascade_dict:
        _widget_type = record["widget_type"]
        _widget_property = record["widget_property"]
        _properties_string = _properties_string + f'\n{_widget_type}: {_widget_property}'

    return _properties_string


def cascade_enabled(palette_id: int) -> bool:
    """The cascade_enabled function, checks for any entries in colour_cascade_properties for the specified palette slot.
    If any exist, it returns True, otherwise it returns False.

    :param palette_id: Palette# of a displayed colour palette
    :return: Boolean.
    """
    if not db_file_exists(db_file_path=DB_FILE_PATH):
        print(f'Unable to locate database file located at {DB_FILE_PATH}')
        raise FileNotFoundError

    db_conn = sqlite3.connect(DB_FILE_PATH)
    cur = db_conn.cursor()
    cur.execute("select count(*) "
                "from colour_cascade_properties "
                "where entry_id = :entry_id", {"entry_id": palette_id})
    _cascade_count_list = cur.fetchall()
    _cascade_count_list, = _cascade_count_list[0]
    db_conn.close()
    if _cascade_count_list:
        return True
    else:
        return False


def colour_dictionary(theme_file: Path) -> dict:
    """Within a theme file CustomTkinter V5, now bundles geometry and colour properties together for each widget.
    We need to filter out the non-colour properties, in addition to the font settings at the end of the theme file.
    This function does that.

    The returned dictionary also has the CTk widget prefix removed, for each widget type, except for CTk()
    widget. This is for display purposes.

    @param theme_file:
    @return: dict"""
    _colour_dictionary = {}
    js = open(theme_file)
    theme_dict = json.load(js)
    for widget_type in SUPPORTED_WIDGETS:
        j_widget_type = widget_type
        for widget_property in COLOUR_PROPERTIES:
            if keys_exist(theme_dict, j_widget_type, widget_property):
                disp_widget = widget_type
                if widget_type != 'CTk':
                    disp_widget = str(widget_type).replace('CTk', '')

                _colour_dictionary[f'{disp_widget}: {widget_property}'] = theme_dict[j_widget_type][widget_property]
    return _colour_dictionary


def delete_preference(db_file_path: Path, scope: str, preference_name):
    """The preference function accepts a preference scope and preference name, and deleted the associated preference
    record from the database.

    :param db_file_path: Database file pathname.
    :param scope: Preference scope / domain code.
    :param preference_name: Preference name."""

    if not db_file_exists(db_file_path=db_file_path):
        print(f'Unable to locate database file located at {db_file_path}')
        raise FileNotFoundError
    db_conn = sqlite3.connect(db_file_path)
    cur = db_conn.cursor()

    cur.execute("delete "
                "from preferences "
                "where scope = :scope "
                "and preference_name = :preference_name;", {"scope": scope, "preference_name": preference_name})
    db_conn.commit()
    db_conn.close()


def hex_to_rgb(hex_colour):
    """ Convert a hex colour code to an RGB tuple."""
    rgb = []
    hex_value = hex_colour.replace('#', '')
    for i in (0, 2, 4):
        decimal = int(hex_value[i:i + 2], 16)
        rgb.append(decimal)

    return tuple(rgb)


def rgb_to_hex(rgb: tuple):
    """Convert RGB tuple to a hex colour code."""
    r, g, b = rgb
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)


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


def scaling_float(scale_pct: str) -> float:
    """Expects a scaling percentage, including the % symbol and converts to a fractional decimal."""
    scaling_float = int(scale_pct.replace("%", "")) / 100
    return scaling_float


def flip_appearance_modes(theme_file_path: Path):
    """Function, which accepts the pathname to a CustomTkinter theme file. It then proceeds to swap
    all light (appearance) mode colours, with those of the dark mode."""
    theme_dict = json_dict(theme_file_path)
    new_theme_dict = copy.deepcopy(theme_dict)
    for widget_type, dict_ in theme_dict.items():
        for property_, value_ in dict_.items():
            if "_color" in property_ and value_ != 'transparent':
                new_theme_dict[widget_type][property_][0] = theme_dict[widget_type][property_][1]
                new_theme_dict[widget_type][property_][1] = theme_dict[widget_type][property_][0]
    with open(theme_file_path, "w") as f:
        json.dump(new_theme_dict, f, indent=2)


def ui_scaling_list():
    return ['70%', '80%', '90%', '100%', '110%', '120%', '130%']


def merge_themes(primary_theme_name: str, primary_mode: str, secondary_theme_name: str, secondary_mode: str,
                 new_theme_name: str, mapped_primary_mode: str = 'Light'):
    """Function, which accepts details of two themes and a new theme name, and merges the two themes, into one new
    theme."""
    theme_json_dir = preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                        preference_name='theme_json_dir')
    primary_file = theme_json_dir / f'{primary_theme_name}.json'
    secondary_file = theme_json_dir / f'{secondary_theme_name}.json'
    new_theme_path = theme_json_dir / f'{new_theme_name}'
    primary_mode_idx = str_mode_to_int(primary_mode)
    secondary_mode_idx = str_mode_to_int(secondary_mode)
    primary_theme_dict = json_dict(primary_file)
    primary_theme_dict = patch_theme(theme_json=primary_theme_dict)
    secondary_theme_dict = json_dict(secondary_file)
    secondary_theme_dict = patch_theme(theme_json=secondary_theme_dict)
    mapped_primary_idx = str_mode_to_int(mapped_primary_mode)
    if mapped_primary_idx == 0:
        mapped_secondary_idx = 1
    else:
        mapped_secondary_idx = 0
    new_theme_dict = copy.deepcopy(primary_theme_dict)
    for widget_type, dict_ in new_theme_dict.items():
        for property_, value_ in dict_.items():
            if "_color" in property_ and value_ != 'transparent':
                new_theme_dict[widget_type][property_][mapped_primary_idx] = primary_theme_dict[widget_type][property_][
                    primary_mode_idx]
                new_theme_dict[widget_type][property_][mapped_secondary_idx] = \
                    secondary_theme_dict[widget_type][property_][secondary_mode_idx]
    with open(new_theme_path, "w") as f:
        json.dump(new_theme_dict, f, indent=2)


def widget_property_split(widget_property: str) -> tuple:
    """Function which accepts a widget property, in the form "<widget_type>: <widget_property>" and breaks out the
    components returning a tuple with <widget_type> and <widget_property>, resurrecting  the "CTk" prefix of the
    widget type, as required for all widgets except CTk().
    @param widget_property:
    @return: tuple"""
    widget_split = widget_property.split(': ')
    widget_type = widget_split[0]
    if widget_type != 'CTk' and widget_type != 'DropdownMenu':
        widget_type = 'CTk' + widget_type
    _property = widget_split[1]
    return widget_type, _property


def widget_member(widget_entries: dict, filter_list: list):
    """Generator method to run through our widgets, primarily in the render_widget_properties method.
    @param widget_entries:
    @param filter_list:
    """
    for property_key in widget_entries:
        if property_key in filter_list:
            yield property_key


def json_dict(json_file_path: Path) -> dict:
    """The json_dict function accepts the pathname to a JSON file, loads the file, and returns a dictionary
    representing the JSON content.
    @rtype: dict
    @param json_file_path:
    @return: dict"""
    with open(json_file_path) as json_file:
        _json_dict = json.load(json_file)
    return _json_dict


def preferences_dict_list(db_file_path: Path):
    """The preferences_dict_list function, extracts all preferences entries as a list of dictionary entries. Each
    dictionary entry represents a row from the preferences table.

    :param db_file_path: Pathname to the sqlite3 database.
    :return list: List of preferences dictionaries.
    """
    if not db_file_exists(db_file_path=db_file_path):
        print(f'Unable to locate database file located at {db_file_path}')
        raise FileNotFoundError

    db_conn = sqlite3.connect(db_file_path)
    db_conn.row_factory = sqlite_dict_factory
    cur = db_conn.cursor()
    cur.execute("select scope, "
                "preference_name, "
                "preference_value, "
                "preference_label, "
                "preference_attr1, "
                "preference_attr2, "
                "preference_attr3 "
                "from preferences "
                "order by scope, preference_name;")
    preferences = cur.fetchall()
    db_conn.close()
    return preferences


def preferences_scope_list(db_file_path: Path, scope: str):
    """The preferences function, returns a list of lists. The inner lists, each represent a row from the preferences
    table, which are matched based on the scope passed to the function.

    :param db_file_path:
    :param scope: The scope/domain to base the list of preferences upon.
    :return: List - each entry is in turn a list, representing a returned row."""

    if not db_file_exists(db_file_path=db_file_path):
        print(f'Unable to locate database file located at {db_file_path}')
        raise FileNotFoundError

    db_conn = sqlite3.connect(db_file_path)
    cur = db_conn.cursor()
    cur.execute("select preference_name, "
                "preference_value, "
                "preference_attr1, "
                "preference_attr2, "
                "preference_attr3, "
                "preference_attr4, "
                "preference_attr5 "
                "from preferences "
                "where scope = :scope "
                "order by preference_name;", {"scope": scope})
    preferences = cur.fetchall()
    db_conn.close()
    list_of_preferences = []
    # We have a list of tuples; each tuple, representing a row.
    for row in preferences:
        record = []
        for column in row:
            record.append(column)
        list_of_preferences.append(record)
    return list_of_preferences


def preference_setting(db_file_path: Path, scope: str, preference_name,
                       default: [str, int, Path] = 'NO_DATA_FOUND') -> any:
    """The preference_setting function accepts a preference scope and preference name, and returns the associated
    preference value.
    :param default:
    :param preference_name:
    :param scope: Preference scope / domain code.
    :param db_file_path: Pathname to the database file.
    :param preference_name: Preference name.
    :return (str): The preference value"""

    if not db_file_exists(db_file_path=db_file_path):
        print(f'Unable to locate database file located at {db_file_path}')
        raise FileNotFoundError

    db_conn = sqlite3.connect(db_file_path)
    cur = db_conn.cursor()

    cur.execute("select preference_value, data_type "
                "from preferences "
                "where scope = :scope "
                "and preference_name = :preference_name;", {"scope": scope, "preference_name": preference_name})
    row = cur.fetchone()
    if row is not None:
        preference_value, data_type = row
    else:
        db_conn.close()
        preference_value = default
        return preference_value
    db_conn.close()
    if data_type == 'str':
        return str(preference_value)
    elif data_type == 'int':
        return int(preference_value)
    elif data_type == 'Path':
        return Path(preference_value)
    elif data_type == 'float':
        return float(preference_value)
    else:
        return str(preference_value)


def scope_preferences(db_file_path: Path, scope: str):
    if not db_file_exists(db_file_path=db_file_path):
        print(f'Unable to locate database file located at {db_file_path}')
        raise FileNotFoundError

    db_conn = sqlite3.connect(db_file_path)
    db_conn.row_factory = sqlite_dict_factory
    cur = db_conn.cursor()

    cur.execute("select scope, preference_name, preference_value, preference_attr1, preference_attr2, preference_attr3 "
                "from preferences "
                "where scope = :scope;", {"scope": scope})
    scope_rows = cur.fetchall()
    db_conn.close()
    return scope_rows


def preference_row(db_file_path: Path, scope: str, preference_name) -> dict:
    """The preference_setting function accepts a preference scope and preference name, and returns the associated row.

    :return (dict): The preference row presented as a dictionary ("column name": value pairs)"""

    if not db_file_exists(db_file_path=db_file_path):
        print(f'Unable to locate database file located at {db_file_path}')
        raise FileNotFoundError

    db_conn = sqlite3.connect(db_file_path)
    db_conn.row_factory = sqlite_dict_factory
    cur = db_conn.cursor()

    cur.execute("select scope, preference_name, preference_value, preference_attr1, preference_attr2, preference_attr3 "
                "from preferences "
                "where scope = :scope "
                "and preference_name = :preference_name;", {"scope": scope, "preference_name": preference_name})
    preference_row = cur.fetchone()
    db_conn.close()
    return preference_row


def sqlite_dict_factory(cursor, row):
    """The sqlite_dict_factory (SQL dictionary factory) method converts a row from a returned sqlite3  dataset
    into a dictionary, keyed on column names.

    :param cursor: sqlite3 cursor
    :param row: list
    :return: dict"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def update_preference_value(db_file_path: Path, scope: str, preference_name, preference_value):
    if not db_file_exists(db_file_path=db_file_path):
        print(f'Unable to locate database file located at {db_file_path}')
        raise FileNotFoundError

    db_conn = sqlite3.connect(db_file_path)
    cur = db_conn.cursor()

    cur.execute("update preferences  "
                "set preference_value = :preference_value "
                "where scope = :scope and preference_name = :preference_name;",
                {"scope": scope, "preference_name": preference_name, "preference_value": preference_value})
    rowcount = cur.rowcount
    db_conn.commit()
    db_conn.close()
    return rowcount


def upsert_preference(db_file_path: Path,
                      preference_row_dict: dict):
    """The upsert_preference function operates as an UPSERT mechanism. Inserting where the preference does not exist,
    but updating where it already exists. We use a dictionary as our row data currency, this helps us preserve column
    values, where we don't modify them if cont required in some contexts.
    :param db_file_path: Pathname to the database file.
    :param preference_row_dict:
    """
    if not db_file_exists(db_file_path=db_file_path):
        print(f'Unable to locate database file located at {db_file_path}')
        raise FileNotFoundError

    db_conn = sqlite3.connect(db_file_path)
    cur = db_conn.cursor()

    # Check to see if the preference exists.
    curr_preference = preference_setting(db_file_path=db_file_path,
                                         scope=preference_row_dict['scope'],
                                         preference_name=preference_row_dict['preference_name'])

    if curr_preference == 'NO_DATA_FOUND':
        # The preference does not exist
        cur.execute("insert  "
                    "into preferences (scope, preference_name, data_type, preference_value, "
                    "preference_attr1, preference_attr2, preference_attr3) "
                    "values "
                    "(:scope, :preference_name, :data_type, :preference_value, "
                    ":preference_attr1, :preference_attr2, :preference_attr3);",
                    preference_row_dict)
    else:
        cur.execute("update preferences  "
                    "set "
                    "    preference_value = :preference_value, "
                    "    preference_attr1 = :preference_attr1, "
                    "    preference_attr2 = :preference_attr2, "
                    "    preference_attr3 = :preference_attr3 "
                    "where scope = :scope and preference_name = :preference_name;",
                    preference_row_dict)

    db_conn.commit()
    db_conn.close()


def new_preference_dict(scope: str, preference_name: str, data_type: str, preference_value,
                        preference_attr1: str = '', preference_attr2: str = '', preference_attr3: str = ''):
    """Creates a new preferences dictionary, which can then be used in conjunction with upsert_preference."""
    preference_dict = {"scope": scope,
                       "preference_name": preference_name,
                       "data_type": data_type,
                       "preference_value": preference_value,
                       "preference_attr1": preference_attr1,
                       "preference_attr2": preference_attr2,
                       "preference_attr3": preference_attr3}

    return preference_dict


def colour_palette_entries(db_file_path: Path):
    if not db_file_exists(db_file_path=db_file_path):
        print(f'Unable to locate database file located at {db_file_path}')
        raise FileNotFoundError

    db_conn = sqlite3.connect(db_file_path)
    db_conn.row_factory = sqlite_dict_factory
    cur = db_conn.cursor()

    cur.execute("select entry_id, row, col, label "
                "from colour_palette_entries "
                "order by entry_id;")
    colour_tiles = cur.fetchall()
    db_conn.close()
    return colour_tiles


def listener_port():
    """The listener_port function obtains and returns the listener port, used for comms from the Control Panel to the
    Preview Panel."""
    _listener_port = preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                        preference_name='listener_port')
    return _listener_port


def method_listener_address():
    _listener_port = listener_port()
    _method_listener_address = (SERVER, _listener_port)
    return _method_listener_address

if __name__ == "__main__":
    colour_dict = colour_dictionary(Path('../assets/themes/GreyGhost.json'))
    widget_prop = 'Button: text_color_disabled'
    print(f'Test the widget_property_split function using {widget_prop}')
    test_widget_type, property = widget_property_split(widget_property=widget_prop)
    print(f'Widget type: {test_widget_type}; Widget property: {property}')
    properties_filter_list_x = ["Button: border_color",
                                "Button: fg_color",
                                "Button: hover_color",
                                "Button: text_color",
                                "Button: text_color_disabled",
                                "CTk: fg_color",
                                "Checkbox: border_color",
                                "Checkbox: checkmark_color",
                                "Checkbox: fg_color",
                                "Checkbox: hover_color",
                                "Checkbox: text_color",
                                "Checkbox: text_color_disabled",
                                "ComboBox: border_color",
                                "ComboBox: button_color",
                                "ComboBox: button_hover_color",
                                "ComboBox: fg_color",
                                "ComboBox: text_color",
                                "ComboBox: text_color_disabled",
                                "DropdownMenu: fg_color",
                                "DropdownMenu: hover_color",
                                "DropdownMenu: text_color",
                                "Entry: border_color",
                                "Entry: fg_color",
                                "Entry: placeholder_text_color",
                                "Entry: text_color",
                                "Frame: border_color",
                                "Frame: fg_color",
                                "Frame: top_fg_color",
                                "Label: fg_color",
                                "Label: text_color",
                                "OptionMenu: button_color",
                                "OptionMenu: button_hover_color",
                                "OptionMenu: fg_color",
                                "OptionMenu: text_color",
                                "OptionMenu: text_color_disabled",
                                "ProgressBar: border_color",
                                "ProgressBar: fg_color",
                                "ProgressBar: progress_color",
                                "Radiobutton: border_color",
                                "Radiobutton: fg_color",
                                "Radiobutton: hover_color",
                                "Radiobutton: text_color",
                                "Radiobutton: text_color_disabled",
                                "ScrollableFrame: label_fg_color",
                                "Scrollbar: button_color",
                                "Scrollbar: button_hover_color",
                                "Scrollbar: fg_color",
                                "SegmentedButton: fg_color",
                                "SegmentedButton: selected_color",
                                "SegmentedButton: selected_hover_color",
                                "SegmentedButton: text_color",
                                "SegmentedButton: text_color_disabled",
                                "SegmentedButton: unselected_color",
                                "SegmentedButton: unselected_hover_color",
                                "Slider: button_color",
                                "Slider: button_hover_color",
                                "Slider: fg_color",
                                "Slider: progress_color",
                                "Switch: button_color",
                                "Switch: button_hover_color",
                                "Switch: fg_color",
                                "Switch: progress_color",
                                "Switch: text_color",
                                "Switch: text_color_disabled",
                                "Textbox: border_color",
                                "Textbox: fg_color",
                                "Textbox: scrollbar_button_color",
                                "Textbox: scrollbar_button_hover_color",
                                "Textbox: text_color",
                                "Toplevel: fg_color"
                                ]
    sorted_widget_properties_x = {'Button: border_color': ['#100000', '#100000'],
                                  'Button: fg_color': ['#48bed4', '#48bed4'],
                                  'Button: hover_color': ['#e1e661', '#e1e661'],
                                  'Button: text_color': ['#000000', '#000000'],
                                  'Button: text_color_disabled': ['#5c5958', '#5c5958'],
                                  'CTk: fg_color': ['#9c4c6b', '#902e56'],
                                  'Checkbox: border_color': ['#b66426', '#b66426'],
                                  'Checkbox: checkmark_color': ['#ffffff', '#ffffff'],
                                  'Checkbox: fg_color': ['#48bed4', '#48bed4'],
                                  'Checkbox: hover_color': ['#e1e661', '#e1e661'],
                                  'Checkbox: text_color': ['#000000', '#000000'],
                                  'Checkbox: text_color_disabled': ['#d9e0e0', '#d9e0e0'],
                                  'ComboBox: border_color': ['#ffffff', '#ffffff'],
                                  'ComboBox: button_color': ['#48bed4', '#48bed4'],
                                  'ComboBox: button_hover_color': ['#5c6063', '#5c6063'],
                                  'ComboBox: fg_color': ['#414343', '#414343'],
                                  'ComboBox: text_color': ['#000000', '#000000'],
                                  'ComboBox: text_color_disabled': ['#d9e0e0', '#d9e0e0'],
                                  'DropdownMenu: fg_color': ['#414343', '#414343'],
                                  'DropdownMenu: hover_color': ['#747676', '#747676'],
                                  'DropdownMenu: text_color': ['#2e2829', '#2e2829'],
                                  'Entry: border_color': ['#000000', '#000000'],
                                  'Entry: fg_color': ['#ccccc9', '#ccccc9'],
                                  'Entry: placeholder_text_color': ['#919090', '#919090'],
                                  'Entry: text_color': ['#000000', '#000000'],
                                  'Frame: border_color': ['#000000', '#000000'],
                                  'Frame: fg_color': ['#9c4c6b', '#9c4c6b'],
                                  'Frame: top_fg_color': ['#4b5c78', '#4b5c78'],
                                  'Label: fg_color': 'transparent',
                                  'Label: text_color': ['#000000', '#000000'],
                                  'OptionMenu: button_color': ['#717476', '#717476'],
                                  'OptionMenu: button_hover_color': ['#505156', '#505156'],
                                  'OptionMenu: fg_color': ['#414343', '#414343'],
                                  'OptionMenu: text_color': ['#2e2829', '#2e2829'],
                                  'OptionMenu: text_color_disabled': ['#d9e0e0', '#d9e0e0'],
                                  'ProgressBar: border_color': ['#000000', '#000000'],
                                  'ProgressBar: fg_color': ['#5c5e59', '#99e15c'],
                                  'ProgressBar: progress_color': ['#c6c8c8', '#e1e661'],
                                  'Radiobutton: border_color': ['#b66426', '#b66426'],
                                  'Radiobutton: fg_color': ['#48bed4', '#48bed4'],
                                  'Radiobutton: hover_color': ['#000000', '#000000'],
                                  'Radiobutton: text_color': ['#50514e', '#e1e661'],
                                  'Radiobutton: text_color_disabled': ['#d9e0e0', '#d9e0e0'],
                                  'ScrollableFrame: label_fg_color': ['#4b5c78', '#4b5c78'],
                                  'Scrollbar: button_color': ['#4e4b49', '#4e4b49'],
                                  'Scrollbar: button_hover_color': ['#1c1e18', '#1c1e18'],
                                  'Scrollbar: fg_color': 'transparent',
                                  'SegmentedButton: fg_color': ['#48bed4', '#48bed4'],
                                  'SegmentedButton: selected_color': ['#e1e661', '#e1e661'],
                                  'SegmentedButton: selected_hover_color': ['#4b5c78', '#4b5c78'],
                                  'SegmentedButton: text_color': ['#000000', '#000000'],
                                  'SegmentedButton: text_color_disabled': ['#d9e0e0', '#d9e0e0'],
                                  'SegmentedButton: unselected_color': ['#9c4c6b', '#9c4c6b'],
                                  'SegmentedButton: unselected_hover_color': ['#000000', '#000000'],
                                  'Slider: button_color': ['#48bed4', '#48bed4'],
                                  'Slider: button_hover_color': ['#000000', '#000000'],
                                  'Slider: fg_color': ['#383e3e', '#99e15c'],
                                  'Slider: progress_color': ['#cccbc9', '#e1e661'],
                                  'Switch: button_color': ['#363639', '#363639'],
                                  'Switch: button_hover_color': ['#50514e', '#50514e'],
                                  'Switch: fg_color': ['#5c5958', '#48bed4'],
                                  'Switch: progress_color': ['#c0c1c0', '#c0c1c0'],
                                  'Switch: text_color': ['#000000', '#000000'],
                                  'Switch: text_color_disabled': ['#d9e0e0', '#d9e0e0'],
                                  'Textbox: border_color': ['#000000', '#000000'],
                                  'Textbox: fg_color': ['#ccccc9', '#ccccc9'],
                                  'Textbox: scrollbar_button_color': ['#48bed4', '#48bed4'],
                                  'Textbox: scrollbar_button_hover_color': ['#e1e661', '#e1e661'],
                                  'Textbox: text_color': ['#000000', '#000000'],
                                  'Toplevel: fg_color': ['#9c4c6b', '#9c4c6b']}

    counter = 0
    member_gen = widget_member(widget_entries=sorted_widget_properties_x, filter_list=properties_filter_list_x)
    for widget_property in member_gen:
        print(f'widget_property = {widget_property}')
        counter += 1
        if counter == 5:
            break

    db_file = Path('../assets/data/ctk_theme_builder.db')
    sample_setting = preference_setting(db_file_path=db_file, scope='window_geometry', preference_name='control_panel')
    print(f'Sample geometry = {sample_setting}')
    sample_row = preference_row(db_file_path=db_file, scope='window_geometry', preference_name='control_panel')
    print(f'Sample geometry row = {sample_row}')
    pref_scope, name, value, _, _, _ = sample_row
    print(f'Scope: {sample_row[pref_scope]}; name: {sample_row[name]}; value: {sample_row[value]}')
    scope_prefs = scope_preferences(db_file_path=db_file, scope='window_geometry')
    print(f'Scope preferences records: {scope_prefs}')
    colour_palettess = colour_palette_entries(db_file_path=db_file)
    print(f'colour_palettess = {colour_palettess}')
    casc_dict = cascade_dict(palette_id=6)
    cascade_count = cascade_enabled(6)
    casc_list = cascade_display_string(palette_id=6)
    print(casc_list)
