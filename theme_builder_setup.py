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
import glob
from os.path import exists
from os.path import expanduser
from zipfile import ZipFile
import zipfile
from datetime import datetime

now = datetime.now()  # current date and time
DATE_STAMP = now.strftime("%Y-%m-%d_%H-%M-%S")

PRODUCT = 'CTk_Theme_Builder'
PRODUCT_NAME = PRODUCT.replace('_', ' ')
__title__ = f'{PRODUCT} Setup'
__author__ = 'Clive Bostock'
__version__ = "2.0.0"

# Constants
ASSET_DIRS = ['etc', 'themes', 'images', 'config', 'palettes', 'views']
KEY_INV_FILES = ['ctk_theme_builder.bat', 'ctk_theme_builder.sh',
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


def log_os_details():
    # Get the operating system name
    os_name = platform.system()

    # Get the operating system version
    os_version = platform.version()
    if os_name == 'Darwin':
        os_name = f'MacOS {os_version}'
    elif os_name == 'Linux':
        os_name = get_linux_distribution(f'{os_name} {os_version}')
    else:
        os_name = f'{os_name} {os_version}'

    lprint(f'\nOperating System: {os_name} {os_version}')


def get_linux_distribution(fallback_os: str):
    try:
        with open('/etc/os-release', 'r') as f:
            for line in f:
                if line.startswith('PRETTY_NAME='):
                    return line.split('=')[1].strip().strip('"')
    except FileNotFoundError:
        return fallback_os


def lprint(output_text: str, inc_newline: bool = True):
    """Function to duplex output across stdout and the logfile."""
    print(output_text)
    if inc_newline:
        LOG_FILE.write(f'{output_text}\n')
    else:
        LOG_FILE.write(f'{output_text}')


class SortingHelpFormatter(HelpFormatter):
    def add_arguments(self, actions):
        actions = sorted(actions, key=attrgetter('option_strings'))
        super(SortingHelpFormatter, self).add_arguments(actions)


ap = argparse.ArgumentParser(formatter_class=SortingHelpFormatter
                             , description=f"""{prog}: The {prog} tool is used to assist in the installation and with 
                             upgrades of {PRODUCT}.""")

ap.add_argument("-i", "--install-location", required=False, action="store",
                help=f"""Used to point to the base install/upgrade location for {PRODUCT_NAME}. {PRODUCT_NAME} will 
                be installed in a {PRODUCT.lower()}, subdirectory below the location provided. If not supplied, 
                a default location will be used. The default install location is assumed to be the user's home 
                directory. For example on MacOS or Linux, this will equate to  $HOME, and on Windows it would be 
                <system_drive>:\\Users\\<username>.""", dest='install_location', default=None)

ap.add_argument("-p", "--package", required=True, action="store",
                help=f"""Used for {PRODUCT_NAME} deployments & upgrades. Use -a along with the pathname to the 
                      {PRODUCT_NAME}  package ZIP file.""", dest='package', default=None)

operating_system = platform.system()
home_directory = expanduser("~")

args_list = vars(ap.parse_args())

package = args_list["package"]
package = os.path.realpath(package)
package_path = Path(package)

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
        lprint('No record of current repo version, assuming 2.0.0')
        registered_app_version = '2.0.0'
    lprint(f'Updating the {PRODUCT_NAME} repository:-')
    lprint(f'Existing repository appears to be version {registered_app_version}...')

    db_conn = sqlite3.connect(db_file_path)
    cur = db_conn.cursor()

    updates_json_file = config_location / 'repo_updates.json'
    updates_json_file = updates_json_file

    with open(updates_json_file) as json_file:
        try:
            updates_dict_list = json.load(json_file)
        except ValueError:
            lprint(f'ERROR: The file, "{updates_json_file}", does not appear to be a valid JSON file.')
            lprint('Bailing out!')
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
        lprint(f'There are {sql_to_apply} potential upgrade actions pending...')
        lprint(f'Backing up ${PRODUCT} repo to: {data_directory}/{backup_repo}')
        shutil.copy(db_file_path, Path(f'{data_directory}/{backup_repo}'))
    else:
        lprint(f'No upgrade actions pending.')

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
                lprint(f'Applying SQL Id: {sql_id}  :- {description} (Succeeded)')
            except sqlite3.OperationalError:
                if version_scalar(sql_apply_version) == version_scalar(app_file_version):
                    # If it fails and the versions are the same, we assume that it's because a DDL
                    # script has been previously run.
                    lprint(f'Apply SQL Id: {sql_id}  :- {description} (FAILED - OperationalError)')
                    raise
            except sqlite3.IntegrityError:
                lprint(f'Error processing SQL (Id = {sql_id}): {sql_statement}')
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
        lprint(f'Invalid number of dots in version string, {version}, a maximum of 2 is expected.')
        lprint('Bailing out!')
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
            lprint(f'Invalid non-integer character, "{component}", found in version string, "{version}" ')
            lprint('Bailing out!')
            exit(1)
        if len(component) > 2:
            lprint(f'Invalid version component, "{component}", found in version string, "{version}"')
            lprint('Maximum version component length expected is 2 characters.')
            lprint('Bailing out!')
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
    # print(f'DEBUG: DB File: {db_file}')
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
        lprint(f'The specified application home directory, {app_home}, appears invalid.\nThe following components '
               f'are missing:')
        for directory in missing_dirs:
            lprint(f'{directory} (directory)')
        for file in missing_files:
            lprint(f'{file} (file)')
        return False
    else:
        return True


def dir_access(directory_path: Path):
    if platform.system() == 'Windows':
        return ''

    if not os.access(install_location, os.R_OK):
        return f'No READ permissions for directory, {install_location}'
    elif not os.access(install_location, os.W_OK):
        return f'No WRITE permissions for directory, {install_location}'
    elif not os.access(install_location, os.X_OK):
        return f'No EXECUTE permissions for directory, {install_location}'

    return ''


def purge_files(directory: Path, file_match: Path):
    """Pattern match and delete files in specified directory."""
    file_list = glob.glob(pathname=f'{directory}/{file_match}')

    for file_path in file_list:
        try:
            lprint(f'Removing previous: {file_path}')
            os.remove(file_path)
        except OSError:
            lprint(f'Failed to delete file: {file_path} (OSError)')


def purge_file(directory: Path, file_name: Path):
    """purge_file purges an individual file, assuming that the file exists."""
    if not os.path.exists(directory / file_name):
        return
    try:
        lprint(f'Removing previous: {directory / file_name}')
        os.remove(directory / file_name)
    except OSError:
        lprint(f'Failed to delete file: {directory / file_name} (OSError)')


def unpack_package(zip_pathname: Path, install_location: Path):
    """"The unpack_package function, is provided for when we need to perform a software upgrade.
    We unpack the wallet contents to the target application home directory, prior to initialisation of the Python
    virtual environment for the application.
    :param zip_pathname:
    :param install_location:
    """
    if not zipfile.is_zipfile(zip_pathname):
        lprint(f'[unpack_package] WARNING: Artefact file, {zip_pathname}, appears to be an invalid ZIP file.')

    with ZipFile(zip_pathname, 'r') as archive:
        extract_location = Path(install_location)
        archive.extractall(extract_location)


if __name__ == "__main__":
    stage_dir = os.getcwd()
    if args_list["install_location"] is None:
        install_location = Path(home_directory)
    else:
        install_location = args_list["install_location"]
        install_location = str(os.path.realpath(install_location))
        install_location = Path(install_location)

    app_home = Path(install_location) / 'ctk_theme_builder'

    if package:
        package = os.path.abspath(package_path)

    LOGFILE_NAME = f'theme_builder_setup_{DATE_STAMP}.log'
    LOG_FILE = open(LOGFILE_NAME, "a")

    # Perform initial checks
    lprint('Checking Python interpreter version...')
    lower_supported = '3.8.0'
    upper_supported = '3.11.99'
    if version_scalar(lower_supported) > version_scalar(python_version):
        print(f'WARNING: Python interpreter version, {python_version}, is unsupported.\n'
              f'Only Python versions before {lower_supported} are not supported')
        exit(1)
    elif version_scalar(python_version) > version_scalar(upper_supported):
        print(f'WARNING: Python interpreter version, {python_version}, is unsupported.\n'
              f'         Only Python versions between {lower_supported} and {upper_supported} are fully supported')
    else:
        print(f'Python version, {python_version}, is a supported version.')

    assets_location = app_home / 'assets'
    data_location = assets_location / 'data'
    temp_location = app_home / 'tmp'
    user_themes_location = app_home / 'user_themes'
    config_location = assets_location / 'config'
    images_location = assets_location / 'images'
    themes_location = assets_location / 'themes'
    etc_location = assets_location / 'etc'
    log_location = app_home / 'log'
    palettes_location = assets_location / 'palettes_location'
    views_location = assets_location / 'views'
    db_file = data_location / f'{PRODUCT.lower()}.db'

    # Check requisite directory permissions
    directory_check = dir_access(directory_path=install_location)
    if directory_check:
        print('ERROR: Cannot install to the specified directory, the directory permissions are insufficient:')
        print(directory_check)
        print(f'The directory must have read, write and execute permissions.')
        exit(1)

    if not install_location.exists() and package is not None:
        print(f'ERROR: The parent directory, {install_location}, for the specified {PRODUCT_NAME} application home, '
              f'does not exist.\nPlease correct the supplied pathname and retry.')
        exit(1)
    elif install_location.exists() and package is None:
        print(
            f'ERROR: For the new application home, you must provide a deployment package via the '
            f'"-a/--package" command modifier.')
        print(f'Please correct and retry.')
        exit(1)

    if package is not None and not package_path.exists():
        lprint(f'ERROR: Cannot locate the specified package ZIP file: {package_path}')
        exit(1)

    greenfield = False
    if app_home.exists():
        action = f'Updating existing application at: {app_home}'
    else:
        # belt n' braces
        action = f'Creating application home: {app_home}'
        greenfield = True
        os.mkdir(app_home)
    # Switch working directory to the application home
    os.chdir(app_home)

    lprint(f'Starting {PRODUCT_NAME} deployment.')
    log_os_details()
    lprint(f'Installation base location: {str(install_location)}')
    lprint(action)

    lprint(f'\n======================== KEY LOCATION MAPPINGS ==========================')
    lprint(f'Package Location: {package}')
    lprint(f'App Home = {app_home}')
    lprint(f'Assets Location = {assets_location}')
    lprint(f'User Theme Location = {user_themes_location}')
    lprint(f'Log Location = {log_location}')
    lprint(f'=========================================================================\n')

    if str(install_location).endswith('ctk_theme_builder') and greenfield:
        lprint(f'\nWARNING: Over-cooked base install location. Install base path includes "ctk_theme_builder".')
        lprint(f'This will cause an application home folder to be {app_home}')
        lprint(
            f"To rectify, delete the upper ctk_theme_builder folder, once the install has finished, and re-run with a simpler install path.\n")
    if not exists(assets_location):
        lprint(f'Creating application assets location: {assets_location}')
        os.mkdir(assets_location)

    if not exists(log_location):
        lprint(f'Creating application assets location: {log_location}')
        os.mkdir(log_location)

    if not exists(temp_location):
        lprint(f'Creating application temp location: {temp_location}')
        os.mkdir(temp_location)

    if not exists(data_location):
        lprint(f'Creating application data location: {data_location}')
        os.mkdir(data_location)

    if not exists(log_location):
        lprint(f'Creating log location: {log_location}')
        os.mkdir(log_location)

    if not exists(user_themes_location):
        lprint(f'Creating user themes location: {user_themes_location}')
        os.mkdir(user_themes_location)

    lprint(f'Checking for repository: {db_file}')
    if not exists(db_file):
        new_database = True
        lprint("Greenfield installation - creating a new repository.")
        initialise_database()
    else:
        lprint("Repository located - pre-existing installation.")

    if package:
        lprint(f'Unpacking package: {package} to: {install_location}')
        # If we are updating from a ZIP file, then first remove old executables
        purge_files(directory=app_home, file_match='*.py')
        purge_files(directory=app_home, file_match='*.sh')
        purge_files(directory=app_home, file_match='*.bat')
        purge_files(directory=app_home / 'lib', file_match='*.py')
        purge_files(directory=app_home / 'lib', file_match='*.sh')
        purge_files(directory=app_home / 'lib', file_match='*.bat')
        purge_files(directory=app_home / 'module', file_match='*.py')
        purge_files(directory=app_home / 'view', file_match='*.py')
        purge_files(directory=app_home / 'controller', file_match='*.py')
        purge_files(directory=app_home / 'utils', file_match='*.sh')
        purge_files(directory=app_home / 'utils', file_match='*.py')
        if operating_system != 'Windows':
            # Remove the ctk_theme_builder.sh -> ctk_theme_builder hard-link.
            # We reinstate it later.
            purge_file(directory=app_home, file_name='ctk_theme_builder')
        unpack_package(zip_pathname=package_path, install_location=install_location)

    version_script = PRODUCT.lower() + '.py'

    lprint(f'Inspecting {PRODUCT_NAME} application home directory...')
    if app_home_contents_ok():
        lprint(f'Install base, {str(os.path.abspath(install_location))}, looks fine.')
    else:
        lprint(f'Install base, {install_location}, does not appear to be correct.')
        exit(1)

    if operating_system == 'Windows':
        lprint('')
        lprint('Launching build_app.bat')
        os.system('.\\build_app.bat > build_app.log 2>&1')

        # Include the build_app.log to the main logfile.
        with open('build_app.log') as f:
            lines = [line for line in f]
            for line in lines:
                lprint(line, inc_newline=False)
        lprint('')
    else:
        lprint('Set execute permissions for scripts')
        os.system('find . -name "*.sh" -exec chmod 750 "{}" ";"')
        lprint('')
        lprint('Launching build_app.sh')
        os.system('./build_app.sh > build_app.log 2>&1')
        # Include the build_app.log to the main logfile.
        with open('build_app.log') as f:
            lines = [line for line in f]
            for line in lines:
                lprint(line, inc_newline=False)
        lprint('')
        lprint('Set execute permissions for ctk_theme_builder')
        os.system('chmod 750 ctk_theme_builder')

    app_version = app_file_version(app_home / 'model' / f'{version_script}')

    apply_repo_updates(data_directory=data_location, app_file_version=app_version, db_file_path=db_file)
    lprint(f'App Home for {PRODUCT_NAME}: ' + str(os.path.abspath(app_home)))

    lprint(f'\nTo launch the application run the ctk_theme_builder command script, located at:')
    lprint(f'{app_home}/ctk_theme_builder')

    print(f'Installation log can be found at: {log_location / LOGFILE_NAME}')
    lprint("\nDone.")
    LOG_FILE.close()
    os.rename(Path(stage_dir) / LOGFILE_NAME, log_location / LOGFILE_NAME)
    os.remove('build_app.log')
