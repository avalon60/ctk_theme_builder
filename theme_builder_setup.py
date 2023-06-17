"""CTk Theme Builder Setup"""

import argparse
from operator import attrgetter
from argparse import HelpFormatter
from pathlib import Path
import json
import shutil
import platform
import sqlite3
import os
from os.path import exists
from os.path import expanduser
from zipfile import ZipFile
import zipfile

PRODUCT = 'CTk_Theme_Builder'
PRODUCT_NAME = PRODUCT.replace('_', ' ')
__title__ = f'{PRODUCT} Setup'
__author__ = 'Clive Bostock'
__version__ = "2.0.0"

# Constants
ASSET_DIRS = ['etc', 'themes', 'images', 'config', 'palettes', 'views']
KEY_INV_FILES = ['ctk_theme_builder.bat', 'ctk_theme_builder.sh', 'ctk_theme_preview.py',
                 'build_app.sh',
                 'build_app.bat', 'get-pip.py', 'requirements.txt',
                 'assets/config/repo_updates.json', 'assets/themes/GreyGhost.json']
python_version = platform.python_version()

prog_path = os.path.realpath(__file__)
prog = os.path.basename(__file__)
if platform.system() == 'Windows':
    os_user_name = os.getlogin()
else:
    os_user_name = os.getenv("LOGNAME")


# Get the data location, required for the config file etc

class SortingHelpFormatter(HelpFormatter):
    def add_arguments(self, actions):
        actions = sorted(actions, key=attrgetter('option_strings'))
        super(SortingHelpFormatter, self).add_arguments(actions)


ap = argparse.ArgumentParser(formatter_class=SortingHelpFormatter
                             , description=f"""{prog}: The {prog} tool is used to assist in the installation and with 
                             upgrades of {PRODUCT}.""")

ap.add_argument("-i", "--install-locations", required=False, action="store",
                help=f"""Used to point to the install/upgrade location for {PRODUCT}. {PRODUCT} will be installed 
                in a {PRODUCT.lower()}, subdirectory below the location provided. If not supplied, a default
                location will be used. The default install location is assumed to be the user's home directory. 
                For example on MacOS or Linux, this will equate to  $HOME, and on Windows it would be 
                <system_drive>:\\Users\\<username>.""", dest='install_location', default=None)


ap.add_argument("-p", "--package", required=False, action="store",
                help=f"""Used for {PRODUCT} deployments & upgrades. Use -a along with the pathname to the {PRODUCT} 
                      package ZIP file.""", dest='package', default=None)


operating_system = platform.system()
home_directory = expanduser("~")

args_list = vars(ap.parse_args())

package = args_list["package"]

if package is not None and not exists(package):
    print(f'ERROR: Cannot locate the specified package ZIP file: {package}')
    exit(1)

b_prog = prog.replace(".py", "")


def app_file_version(python_file: Path):
    """Given a Python program, find the version, as defined by __version__."""
    with open(python_file, 'r') as fp:
        # read all lines in a list
        lines = fp.readlines()
        for line in lines:
            # check if string present on a current line
            if '__version__' in line:
                version_line = line
                break
    version_list = version_line.split()
    if len(version_list) == 3:
        version = version_list[2]
    else:
        return 'unknown'
    return version.replace('"', '')


def apply_repo_updates(data_directory: Path, app_file_version: str, db_file_path: Path):
    """Perform any system related data related migration steps required. This avoids the necessity of performing a
    complicated migration, where data structures require change."""

    registered_app_version, _ = app_versions()
    if registered_app_version is None:
        print('No record of current repo version, assuming 2.0.0')
        registered_app_version = '2.0.0'
    print(f'Updating the {PRODUCT} repository:-')
    print(f'Existing repository appears to be version {registered_app_version}...')

    db_conn = sqlite3.connect(db_file_path)
    cur = db_conn.cursor()

    updates_json_file = config_location / 'repo_updates.json'
    updates_json_file = updates_json_file

    with open(updates_json_file) as json_file:
        try:
            updates_dict_list = json.load(json_file)
        except ValueError:
            print(f'ERROR: The file, "{updates_json_file}", does not appear to be a valid JSON file.')
            print('Bailing out!')
            raise
        except IOError:
            feedback = f'Failed to read file {updates_json_file} - possible permissions issue.'

    sql_to_apply = 0
    for sql_id in updates_dict_list:
        sql_apply_version = updates_dict_list[sql_id]["sql_apply_version"]
        if version_scalar(registered_app_version) < version_scalar(sql_apply_version) <= version_scalar(
                app_file_version):
            sql_to_apply += 1

    backup_repo = (f'{PRODUCT.lower()}-{registered_app_version}.db')
    # If changes are to be made to the repo, and this is not a greenfield
    # deployment, then take a backup of the repo, as a safety measure.
    if sql_to_apply > 0 and registered_app_version != '1.9.9':
        print(f'There are {sql_to_apply} potential upgrade actions pending...')
        print(f'Backing up ${PRODUCT} repo to: {data_directory}/{backup_repo}')
        shutil.copy(db_file_path, Path(f'{data_directory}/{backup_repo}'))
    else:
        print(f'No upgrade actions pending.')

    sql_count = 0
    for sql_id in updates_dict_list:
        description = updates_dict_list[sql_id]["description"]
        sql_statement = updates_dict_list[sql_id]["sql_statement"]
        sql_statement = sql_statement.replace('%os_user_name%', os_user_name)
        sql_statement = sql_statement.replace('%user_themes_location%', str(user_themes_location))
        sql_apply_version = updates_dict_list[sql_id]["sql_apply_version"]
        if version_scalar(registered_app_version) < version_scalar(sql_apply_version) <= version_scalar(
                app_file_version):
            try:
                cur.execute(sql_statement)
                print(f'Applying SQL Id: {sql_id}  :- {description} (Succeeded)')
            except sqlite3.OperationalError:
                if version_scalar(sql_apply_version) == version_scalar(app_file_version):
                    # If it fails and the versions are the same, we assume that it's because a DDL
                    # script has been previously run.
                    print(f'Apply SQL Id: {sql_id}  :- {description} (FAILED - OperationalError)')
                    raise
            except sqlite3.IntegrityError:
                print(f'Error processing SQL (Id = {sql_id}): {sql_statement}')
                raise
            sql_count += 1
    print(f'Repo updates applied: {sql_count}')
    # Upsert preference opens the database, so ensure we close it here, to avoid a lock error,
    db_conn.commit()
    db_conn.close()
    update_app_version(new_app_version=app_file_version)


def version_scalar(version: str):
    """Version scalar, takes a version number (with dot notation) and converts it to a scalar. The number of components
    within the version, is by default assumed to be 3. If you specifiy a shorter version format (e.g. 3.1), then it will
    be augmented to 3 components (3.1.0), before converting and returning the scalar value."""
    dot_count = version.count('.')
    if dot_count > 2:
        print(f'Invalid number of dots in version string, {version}, a maximum of 2 is expected.')
        print('Bailing out!')
        exit(1)

    version_padded = version
    for i in range(3 - dot_count - 1):
        version_padded = version + '.0'
    version_list = version_padded.split('.')
    # Check version components are all integers...
    for component in version_list:
        try:
            comp = int(component)
        except ValueError:
            print(f'Invalid non-integer character, "{component}", found in version string, "{version}" ')
            print('Bailing out!')
            exit(1)
        if len(component) > 2:
            print(f'Invalid version component, "{component}", found in version string, "{version}"')
            print('Maximum version component length expected is 2 characters.')
            print('Bailing out!')
            exit(1)

    scalar_version = ''
    for component in version_list:
        component = component.zfill(2)
        scalar_version = scalar_version + component
    return int(scalar_version)


def initialise_database():
    """The initialise_database function created the sqllite3 database, used to store DCCM settings. This is executed
    when the program is first run.

    :param db_file_path: Pathname of the sqllite3 database, to be created."""
    print(f'DEBUG: DB File: {db_file}')
    db_conn = sqlite3.connect(db_file)
    cur = db_conn.cursor()

    cur.execute("""create table if not exists 
     preferences (
       scope            text not null,
       preference_name  text not null,
       preference_value text not null,
       data_type        text not null,
       preference_attr1 text,
       preference_attr2 text,
       preference_attr3 text,
       primary key (scope, preference_name)
   )
    """)

    db_conn.commit()

    # This is a single record table.
    # The record_number column will always be set to 1.
    cur.execute("""create table if not exists
     application_control (
       record_number            integer primary key,
       app_version text,
       previous_app_version     text);""")
    cur.execute("insert into application_control (record_number, app_version, previous_app_version) values (1, "
                "'1.9.9', '1.9.9');")

    cur.execute("""create table if not exists
                   colour_palette_entries (
                        entry_id                  int primary key,
                        row                       int,
                        col                       int,
                        label                     text);""")

    cur.execute("""create table if not exists
                    colour_cascade_properties (
                        entry_id               int,
                        widget_type            text,
                        widget_property        text,
                        primary key (entry_id, widget_type, widget_property));""")

    db_conn.commit()

def preference(db_file_path: Path, scope: str, preference_name):
    """The preference function accepts a preference scope and preference name, and returns the associated preference
    value.
    :param db_file_path: (Path) Pathname to the DCCM database file.
    :param scope: (str) Preference scope / domain code.
    :param preference_name: (str) Preference name.
    :return: (str) The preference value
    """
    db_conn = sqlite3.connect(db_file_path)
    cur = db_conn.cursor()

    cur.execute("select preference_value "
                "from preferences "
                "where scope = :scope "
                "and preference_name = :preference_name;", {"scope": scope, "preference_name": preference_name})
    preference_value = cur.fetchone()
    if preference_value is not None:
        preference_value, = preference_value
    db_conn.close()
    return preference_value


def app_versions():
    """The preference obtains and retrns the current and previous application versions, returning as a tuple.
    value.
    :return: (tuple) The app_version, previous_app_version
    """
    db_conn = sqlite3.connect(db_file)
    cur = db_conn.cursor()

    cur.execute("select app_version, previous_app_version "
                "from application_control "
                "where record_number = 1")
    record = cur.fetchone()
    if record is not None:
        application_version, previous_app_version = record
    else:
        previous_app_version, application_version = '0.0.0', '2.0.0'


    db_conn.close()
    return application_version, previous_app_version


def update_app_version(new_app_version: str):
    db_conn = sqlite3.connect(db_file)
    cur = db_conn.cursor()
    application_version, previous_app_version = app_versions()
    if new_app_version == application_version:
        # We don't want to enb up with previous_app_version = app_version
        return
    cur.execute("update application_control "
                "set  previous_app_version = app_version "
                "where record_number = 1;")
    cur.execute("update application_control "
                "set  app_version = :app_version "
                "where record_number = 1;", {"app_version": new_app_version})
    db_conn.commit()
    db_conn.close()


def upsert_preference(db_file_path: Path,
                      scope: str,
                      preference_name: str,
                      preference_value: str,
                      data_type: str):
    """The upsert_preference function operates as an UPSERT mechanism. Inserting where the preference does not exists,
    but updating where it already exists.

    :param db_file_path:
    :param data_type:
    :param scope: A string, defining the preference scope/domain.
    :param preference_name: The preference withing the specified scope, to be inserted/updated.
    :param preference_value: The new value to set."""
    db_conn = sqlite3.connect(db_file_path)
    cur = db_conn.cursor()

    # Check to see if the preference exists.
    pref_exists = preference(db_file_path=db_file_path, scope=scope, preference_name=preference_name)


    if pref_exists is None:
        # The preference does not exist
        cur.execute("insert  "
                    "into preferences (scope, preference_name, data_type, preference_value) "
                    "values "
                    "(:scope, :preference_name, :preference_value, :data_type);",
                    {"scope": scope, "preference_name": preference_name,
                     "data_type": data_type, "preference_value": preference_value})
    else:
        cur.execute("update preferences  "
                    "set preference_value = :preference_value, "
                    "    data_type = :data_type "
                    "where scope = :scope and preference_name = :preference_name;",
                    {"scope": scope,
                     "preference_name": preference_name,
                     "preference_value": preference_value,
                     "data_type": data_type})

    db_conn.commit()
    db_conn.close()


def app_home_contents_ok():
    """Function to check the home contents, to ensure that it looks like a valid application home directory.
    If components are missing we list (print) them and return False. Otherwise, we return True."""
    missing_dirs = []
    missing_files = []
    for directory in ASSET_DIRS:
        full_path = assets_location / directory
        if not full_path.exists():
            missing_dirs.append(full_path)
    for file in KEY_INV_FILES:
        full_path = app_home / file
        if not full_path.exists():
            missing_files.append(full_path)
    if len(missing_files) > 0 or len(missing_dirs) > 0:
        print(f'The specified application home directory, {app_home}, appears invalid.\nThe following components '
              f'are missing:')
        for directory in missing_dirs:
            print(f'{directory} (directory)')
        for file in missing_files:
            print(f'{file} (file)')
        return False
    else:
        return True


def unpack_package(zip_pathname: Path, install_location: Path):
    """"The unpack_package function, is provided for when we need to perform a software upgrade.
    We unpack the wallet contents to the target application home directory, prior to initialisation of the Python
    virtual environment for the application.
    :param zip_pathname:
    :param install_location:
    """
    if not zipfile.is_zipfile(zip_pathname):
        print(f'unpack_package: Artefact file, {zip_pathname}, appears to be an invalid ZIP file. Unable to proceed!')
        exit(1)

    with ZipFile(zip_pathname, 'r') as archive:
        extract_location = Path(install_location)
        archive.extractall(extract_location)


if __name__ == "__main__":
    if args_list["install_location"] is None:
        install_location = Path(home_directory) / 'ctk_theme_builder'
    else:
        install_location = args_list["install_location"]
        install_location = str(os.path.abspath(install_location))
        install_location = Path(install_location)
    
    if package:
        package = os.path.abspath(package)

    print(f'Starting {PRODUCT} deployment.')
    print(f'Application home: {str(install_location)}')

    # Perform initial checks
    print('Checking Python interpreter version...')
    if not (version_scalar('3.8.0') <= version_scalar(python_version) <= version_scalar('3.10.99')):
        print(f'ERROR: Python interpreter version, {python_version}, is unsupported.\n'
              f'Only Python versions between 3.8 and 3.10 are supported')
        exit(1)
    else:
        print(f'Python version, {python_version}, is a supported version.')

    app_home = Path(os.path.abspath(install_location))
    # Switch working directory to the application home
    os.chdir(app_home)

    app_home = install_location / 'ctk_theme_builder'
    assets_location = app_home / 'assets'
    data_location = assets_location / 'data'
    temp_location = app_home / 'tmp'
    user_themes_location = app_home / 'user_themes'
    config_location = assets_location / 'config'
    images_location = assets_location / 'images'
    themes_location = assets_location / 'themes'
    etc_location = assets_location / 'etc'
    palettes_location = assets_location / 'palettes_location'
    views_location = assets_location / 'views'
    db_file = data_location / f'{PRODUCT.lower()}.db'

    if not exists(install_location) and package is not None:
        if exists(install_location):
            print(f'Creating application home: {app_home}')
            os.mkdir(app_home)
        else:
            print(f'ERROR: The parent directory, {install_location}, for the specified {PRODUCT} application home, '
                  f'does not exist.\nPlease correct the supplied pathname and retry.')
            exit(1)
    elif not exists(install_location) and package is None:
        print(
            f'ERROR: For the new application home, {install_location}, you must provide a deployment package via the '
            f'"-a/--package" command modifier.')
        print(f'Please correct and retry.')
        exit(1)

    if app_home.exists():
        print(f'Updating existing application at: {app_home}')
    else:
        # belt n' braces
        print(f'Creating application home: {app_home}')
        os.mkdir(app_home)

    if not exists(assets_location):
        print(f'Creating application assets location: {assets_location}')
        os.mkdir(assets_location)

    if not exists(temp_location):
        print(f'Creating application temp location: {temp_location}')
        os.mkdir(temp_location)

    if not exists(data_location):
        print(f'Creating application data location: {data_location}')
        os.mkdir(data_location)

    if not exists(user_themes_location):
        print(f'Creating user themes location: {user_themes_location}')
        os.mkdir(user_themes_location)


    print(f'Checking for repository: {db_file}')
    if not exists(db_file):
        new_database = True
        print("Greenfield installation - creating a new repository.")
        initialise_database()

    if package:
        print(f'Unpacking package: {package} to: {install_location}')
        unpack_package(zip_pathname=package, install_location=install_location)

    entry_point_script = PRODUCT.lower() + '.py'

    print(f'Inspecting {PRODUCT} application home directory...')
    if app_home_contents_ok():
        print(f'Install base, {str(os.path.abspath(install_location))}, looks fine.')
    else:
        print(f'Install base, {install_location}, does not appear to be correct.')
        exit(1)

    os.chdir(app_home)
    if operating_system == 'Windows':
        os.system('.\\build_app.bat')
    else:
        os.system('chmod 750 *.sh')
        os.system('./build_app.sh')
        os.system('chmod 750 ctk_theme_builder')

    app_version = app_file_version(app_home / f'{entry_point_script}')

    apply_repo_updates(data_directory=data_location, app_file_version=app_version, db_file_path=db_file)
    print(f'App Home for {PRODUCT}: ' + str(os.path.abspath(app_home)))

    print(f'\nTo launch the application run the ctk_theme_builder command script, located at:\n{app_home}/ctk_theme_builder')

    print("\nDone.")

