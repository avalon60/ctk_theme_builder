__title__ = 'CB CustomTkinter Theme Builder Preferences Module'
__author__ = 'Clive Bostock'
__license__ = 'MIT - see LICENSE.md'

from pathlib import Path
import customtkinter as ctk
import sqlite3
import os



# Constants
APP_HOME = os.path.dirname(os.path.realpath(__file__))
APP_HOME = Path(os.path.dirname(APP_HOME))
CTK_SITE_PACKAGES = Path(ctk.__file__)
CTK_SITE_PACKAGES = os.path.dirname(CTK_SITE_PACKAGES)
CTK_ASSETS = CTK_SITE_PACKAGES / Path('assets')
CTK_THEMES = CTK_ASSETS / 'themes'

ASSETS_DIR = APP_HOME / 'assets'
CONFIG_DIR = ASSETS_DIR / 'config'
APP_DATA_DIR = ASSETS_DIR / 'data'
DB_FILE_PATH = APP_DATA_DIR / 'ctk_theme_builder.db'
LOG_DIR = APP_HOME / 'log'

db_file_found = None


def all_widget_categories(widget_attributes):
    """This function receives a dictionary, based on JSON theme builder view file content,
    and scans it, to build a list of all the widget categories included in the view. The categories
    are the select options we see, in the Filter View drop-down list, once we have selected a Properties View."""
    categories = []
    for category in widget_attributes:
        categories.append(category)
    categories.sort()
    return categories


def db_file_exists(db_file_path: Path):
    global db_file_found
    if db_file_found is None:
        if db_file_path.exists():
            db_file_found = True
        else:
            db_file_found = False
    return db_file_found


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


def preference_setting(scope: str, preference_name, db_file_path: Path = DB_FILE_PATH,
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





if __name__ == "__main__":
    pass
