"""Logging library."""

# Usage:
#
# from lib.loggerutl import LogGen
#
# Then instantiate a logger:
#
#     context.logger = LogGen().logger_gen()
#
#  Optionally you can override defaults for the logger_name and/or log_file:
#
#     context.logger = LogGen().logger_gen(logger_name='AutoTesting', log_file='mylog.log')
#
# Log messages:
#
# context.logger.debug('Debug message')
# context.logger.info('Info message') etc.

import os
import sqlite3
import sys
import threading
import tkinter as tk
from loguru import logger as logr
from pathlib import Path
import datetime
import time
import ctk_tb.model.preferences as pref
import ctk_tb.paths as app_paths

APP_HOME = app_paths.INSTALL_ROOT
LOG_DIR = app_paths.LOG_DIR
ASSETS_DIR = app_paths.ASSETS_DIR
APP_DATA_DIR = app_paths.STATE_DIR
DB_FILE_PATH = app_paths.DB_FILE_PATH
RUNTIME_LOG = "runtime.log"

# Initialise the log stamp integer.
now = datetime.datetime.now()
LOG_STAMP = int(round(time.time() * 1000))
LOG_SEP = '|'

LOG_LEVELS = ['TRACE', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
LOG_LEVEL_DISP = []
for level in LOG_LEVELS:
    LOG_LEVEL_DISP.append(level.title())


# Declare exceptions
class InvalidLoggerLevel(Exception):
    pass


logger = logr
run_stamp = None


def _safe_preference_setting(scope: str, preference_name: str, default):
    """Return a preference value or the supplied default before runtime init exists."""
    try:
        return pref.preference_setting(scope=scope, preference_name=preference_name, default=default)
    except (FileNotFoundError, sqlite3.Error):
        return default

# Get custom login level colours
supplementary_colour = _safe_preference_setting(scope='logger', preference_name='supplementary',
                                                default="light-green")
scenario_started_colour = _safe_preference_setting(scope='logger', preference_name='scenario_started',
                                                   default="light-blue")
scenario_completed_colour = _safe_preference_setting(scope='logger', preference_name='scenario_completed',
                                                     default="light-blue")

log_level_code = _safe_preference_setting(scope='logger', preference_name='log_level', default="Info")
log_level_code = log_level_code.upper()
log_stamping = _safe_preference_setting(scope='logger', preference_name='log_stamping', default="Yes")
inc_stderr = _safe_preference_setting(scope='logger', preference_name='log_stderr', default="Yes")

log_filename = _safe_preference_setting(scope='logger', preference_name='log_filename', default=RUNTIME_LOG)

# Configure custom log levels
logr.level("STARTED", no=21, color=f"<{scenario_started_colour}>", icon="")
logr.level("COMPLETED", no=22, color=f"<{scenario_completed_colour}>", icon="")
logr.level("SUPPLEMENTARY", no=23, color=f"<{supplementary_colour}>", icon="")

logr.remove()
# log_format ='<green>{time:DD/MM/YYYY HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{' \
#             'name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>'
log_format = '<green>{time:DD/MM/YYYY HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>'

if log_stamping.lower() == 'Yes':
    if inc_stderr == 'Yes':
        logr.add(sink=sys.stderr, level=log_level_code,
                 format=log_format,
                 backtrace=True,
                 diagnose=True)
    if LOG_DIR.exists():
        logr.add(sink=Path(f"{LOG_DIR}/{log_filename}"), level=log_level_code,
                 format=log_format,
                 backtrace=True,
                 diagnose=True)
    log = logr.bind(ls=LOG_STAMP)
else:
    if inc_stderr == 'Yes':
        logr.add(sink=sys.stderr, level=log_level_code,
                 format=log_format,
                 backtrace=True,
                 diagnose=True)
    if LOG_DIR.exists():
        logr.add(sink=Path(f"{LOG_DIR}/{log_filename}"), level=log_level_code,
                 format="{time:DD/MM/YYYY HH:mm:ss.SSS} | {level} | {message}",
                 backtrace=True,
                 diagnose=True)
    log = logr

log.info(f'[lib.loggerutl] Logging enabled with a logging level of: {log_level_code}')
logger = log


def _log_unhandled_exception(exc_type, exc_value, exc_traceback) -> None:
    """Log an uncaught exception with its full traceback."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.opt(exception=(exc_type, exc_value, exc_traceback)).critical('Unhandled exception')


def install_exception_logging() -> None:
    """Install process-wide exception hooks for uncaught exceptions."""
    sys.excepthook = _log_unhandled_exception

    if hasattr(threading, 'excepthook'):
        def _thread_exception_hook(args) -> None:
            _log_unhandled_exception(args.exc_type, args.exc_value, args.exc_traceback)

        threading.excepthook = _thread_exception_hook


install_exception_logging()


def install_tk_callback_logging() -> None:
    """Install global Tk callback exception logging.

    Tkinter widget callbacks do not flow through ``sys.excepthook``. They are
    routed through ``Tk.report_callback_exception`` instead, which by default
    prints to stderr. Override that handler so Tk callback stacks are written to
    the runtime log.
    """

    def _report_callback_exception(self, exc, val, tb) -> None:
        logger.opt(exception=(exc, val, tb)).error('Unhandled Tk callback exception')

    tk.Tk.report_callback_exception = _report_callback_exception


install_tk_callback_logging()

def truncate_log():
    """Clear down the runtime log."""
    with open(LOG_DIR / RUNTIME_LOG, "w") as f:
        f.truncate(0)  # Truncate the file to 0 bytes

def logfile_size():
    file_size = os.path.getsize(LOG_DIR / RUNTIME_LOG)
    return file_size

def db_file_exists(db_file_path: Path):
    return db_file_path.exists()


def format_log_text(log_text, class_name: str = None, method_name: str = None) -> str:
    if log_text:
        sep = ':'
    else:
        sep = ''

    if class_name and method_name:
        log_text = f'[{class_name}.{method_name}]: {log_text}'
    elif class_name:
        log_text = f'[{class_name}]{sep} {log_text}'
    elif method_name:
        log_text = f'[{method_name}]{sep} {log_text}'
    return log_text


def log_stamp(post_underscore: bool = True, pref_underscore: bool = False) -> str:
    """This function returns the log stamp, which is generated when the step file starts to execute. The log stamp is
    a date/time based integer, which can be included to file name and log entry formats, assuming that the config.ini
    entry, log_stamping is set to y. If log_stamping is disabled (set to n), then we return an empty string.
    :param post_underscore: If set to True (default is True), the return string is post-fixed with an underscore.
    :param pref_underscore: If set to True (default is False), the return string is prefixed with an underscore.
    :return str: log stamp string.
    """
    log_stamping = pref.preference_setting(db_file_path=DB_FILE_PATH, scope='logger',
                                           preference_name='log_stamping')
    _log_stamp = LOG_STAMP
    if post_underscore:
        _log_stamp = str(_log_stamp) + '_'

    if pref_underscore:
        _log_stamp = '_' + str(_log_stamp)

    if log_stamping.lower() == 'y':
        return _log_stamp
    else:
        return ''


def log_supplementary(supplementary_text: str):
    """Function to log supplementary text to the log. Using this function, ensures more standard format for the
    log entries.
    :param supplementary_text:
    """
    # This function leverages a loguru custom log level.
    logger.log("SUPPLEMENTARY", f'{supplementary_text}')


def log_success(class_name: str, method_name: str = None, supplementary_text: str = '') -> None:
    """Function to log a BDD step success. Using this function, ensures more standard format for the log entries.
    If specified, supplementary text is added as a secondary log entry.
    :param method_name:
    :param class_name
    :param supplementary_text
    """
    log_text = ''
    if class_name or method_name:
        log_text = format_log_text(log_text='', class_name=class_name, method_name=method_name)
    logger.success(f'{log_text}')
    if supplementary_text:
        log_supplementary(supplementary_text=supplementary_text)


def log_critical(log_text, supplementary_text: str = None, class_name: str = None, method_name: str = None) -> None:
    """Function to log a  failure. Using this function, ensures more standard format for the log entries.
    If specified, supplementary text is added as a secondary log entry.
    :param method_name:
    :param class_name:
    :param log_text
    :param supplementary_text
    """

    if class_name or method_name:
        log_text = format_log_text(log_text=log_text, class_name=class_name, method_name=method_name)
    logger.critical(log_text)
    if supplementary_text:
        log_supplementary(supplementary_text=supplementary_text)


def log_exception(exception):
    if isinstance(exception, BaseException):
        logger.opt(exception=exception).error(str(exception))
    else:
        logger.exception(exception)


def log_debug(log_text, supplementary_text: str = None, class_name: str = None, method_name: str = None) -> None:
    """Function to log a  failure. Using this function, ensures more standard format for the log entries.
    If specified, supplementary text is added as a secondary log entry.
    :param log_text:
    :param supplementary_text:
    :param class_name:
    :param method_name:
    """

    if class_name or method_name:
        log_text = format_log_text(log_text=log_text, class_name=class_name, method_name=method_name)
    logger.debug(log_text)
    if supplementary_text:
        log_supplementary(supplementary_text=supplementary_text)


def log_error(log_text, supplementary_text: str = None, class_name: str = None, method_name: str = None) -> None:
    """Function to log a  failure. Using this function, ensures more standard format for the log entries.
    If specified, supplementary text is added as a secondary log entry.
    :param log_text:
    :param supplementary_text:
    :param class_name:
    :param method_name:
    """

    if class_name or method_name:
        log_text = format_log_text(log_text=log_text, class_name=class_name, method_name=method_name)

    logger.error(log_text)

    if supplementary_text:
        log_supplementary(supplementary_text=supplementary_text)


def log_warning(log_text, supplementary_text: str = None, class_name: str = None, method_name: str = None) -> None:
    """Function to log a warning. Using this function, ensures more standard format for the log entries.
    If specified, supplementary text is added as a secondary log entry.
    :param method_name:
    :param class_name:
    :param log_text:
    :param supplementary_text:
    """

    if class_name or method_name:
        log_text = format_log_text(log_text=log_text, class_name=class_name, method_name=method_name)

    logger.warning(log_text)

    if supplementary_text:
        log_supplementary(supplementary_text=supplementary_text)


def log_info(log_text: str, class_name: str = None, method_name: str = None) -> None:
    """Function to log a free format log entry. Use judiciously, as we need to aspire to a common format!
    :param log_text:
    :param class_name:
    :param method_name:
    """

    if class_name or method_name:
        log_text = format_log_text(log_text=log_text, class_name=class_name, method_name=method_name)

    logger.info(f'{log_text}')


def log_complete(class_name: any, supplementary_text: str = None) -> None:
    """Function to log the start of a feature's step file execution. Using this function, ensures more standard format
    for the log entries.
    :param class_name:
    :param supplementary_text: """
    # This function leverages a loguru custom log level.

    log_text = ''
    if class_name:
        log_text = format_log_text(log_text=log_text, class_name=class_name)

    logger.log("COMPLETED", f'{class_name}')
    if supplementary_text:
        log_supplementary(supplementary_text=supplementary_text)


def log_started(class_name: any, supplementary_text: str = None) -> None:
    """Function to log the start of a feature's step file execution. Using this function, ensures more standard format
    for the log entries.
    :param class_name:
    :param supplementary_text: """
    # This function leverages a loguru custom log level.

    log_text = ''
    if class_name:
        log_text = format_log_text(log_text=log_text, class_name=class_name)

    logger.log("STARTED", f'{log_text}')
    if supplementary_text:
        log_supplementary(supplementary_text=supplementary_text)


if __name__ == '__main__':
    print(f'Log stamp: {log_stamp()}')
