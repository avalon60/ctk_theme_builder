__title__ = 'CTk Theme Builder'
__author__ = 'Clive Bostock'
__license__ = 'MIT - see LICENSE.md'

# A hat tip and thankyou, to Tom Schimansky for is excellent work with CustomTkinter.
# Credit to my friend and colleague Jan Bejec, as well as my wife for their contributions to my logo.
# Also, a thankyou to Akash Bora for producing the excellent CTkToolTip and CTkMessagebox widgets.

import argparse
from view.control_panel import ControlPanel
from argparse import HelpFormatter
from operator import attrgetter
import os
import re
from view.ctk_theme_preview import PreviewPanel
from model.ctk_theme_builder import log_call

# import lib.CTkMessagebox.ctkmessagebox

DEBUG = 0

preview_panel = None
PROG = os.path.basename(__file__)


@log_call
def valid_theme_name(theme_name):
    pattern = re.compile(r"[A-Za-z0-9_()\s]+")
    if pattern.fullmatch(theme_name):
        return True
    else:
        return False


@log_call
def all_widget_attributes(widget_attributes):
    """This function receives a dictionary, based on JSON theme builder view file content,
    and scans it, to build a list of all the widget properties included in the view."""
    all_attributes = []
    for value_list in widget_attributes.values():
        all_attributes = all_attributes + value_list
    return all_attributes


def run_preview_panel(appearance_mode, theme_file):
    """ Function to launch the preview panel."""
    global preview_panel
    preview_panel = PreviewPanel(appearance_mode=appearance_mode, theme_file=theme_file)


class SortingHelpFormatter(HelpFormatter):
    def add_arguments(self, actions):
        actions = sorted(actions, key=attrgetter('option_strings'))
        super(SortingHelpFormatter, self).add_arguments(actions)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(formatter_class=SortingHelpFormatter
                                 , description=f"{PROG}: Welcome to CTk Theme Designer, which is designed to help you "
                                               f"design, themes to run with the CustomTkinter framework")

    ap.add_argument("-a", '--set-appearance', required=False, action="store",
                    help="Set the CustomTkinter appearance mode. Used for colour preview only.",
                    dest='appearance_mode', default='Dark')

    ap.add_argument("-t", '--set-theme', required=False, action="store",
                    help="Set the CustomTkinter theme. Used for colour preview only.",
                    dest='theme_file', default=None)

    args_list = vars(ap.parse_args())
    appearance_mode = args_list["appearance_mode"]
    theme_file = args_list["theme_file"]

    # If theme is set, we assume we are running in "preview" mode.
    if theme_file is not None:
        running_preview = True
        run_preview_panel(appearance_mode=appearance_mode, theme_file=theme_file)
    else:
        controller = ControlPanel()
