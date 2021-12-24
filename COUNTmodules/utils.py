#!/usr/bin/env python3
"""
General utility functions in gcount-tasks.
Functions:
    valid_path_to() - Get absolute path to files and directories.
    position_wrt_main() - Set coordinates of a tk.Toplevel window
        relative to root window position.
    enter_only_digits() - Constrain tk.Entry() values to digits.

    Copyright (C) 2020-2021  C. Echt

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see https://www.gnu.org/licenses/.
"""
__author__ = 'cecht, BOINC ID: 990821'
__copyright__ = 'Copyright (C) 2020-2021 C. Echt'
__license__ = 'GNU General Public License'
__program_name__ = 'gcount-tasks, count-tasks'
__version__ = '0.0.1'
__dev_environment__ = "Python 3.8 - 3.9"
__project_url__ = 'https://github.com/csecht/CountBOINCtasks'
__maintainer__ = 'cecht'
__status__ = 'Development Status :: 4 - Beta'

import sys
from pathlib import Path


def valid_path_to(relative_path: str) -> Path:
    """
    Get absolute path to files and directories.
    _MEIPASS var is used by distribution programs from
    PyInstaller (--onefile or --windowed), e.g. for an images directory.

    :param relative_path: File or dir name path, as string.
    :return: Absolute path as pathlib Path object.
    """
    # Modified from: https://stackoverflow.com/questions/7674790/
    #    bundling-data-files-with-pyinstaller-onefile and PyInstaller manual.
    if getattr(sys, 'frozen', False):  # hasattr(sys, '_MEIPASS'):
        base_path = getattr(sys, '_MEIPASS', Path(Path(__file__).resolve()).parent)
        return Path(base_path) / relative_path
    return Path(relative_path).resolve()


def position_wrt_main(mainwin, mod_x=0, mod_y=0) -> str:
    """
    Gets screen position of *mainwin* and applies optional offsets.
    Used to set screen position of a Toplevel object with respect to
    the main/root window position. Use with the geometry() method,
    example: mytopwin.geometry(utils.position_wrt_main(root, 15, -15))

    :param mainwin: The main window object (e.g., 'root', 'main', or
                    'app') for which to get screen pixel coordinates.
    :param mod_x: optional pixels to add/subtract to *mainwin* x coordinate.
    :param mod_y: optional pixels to add/subtract to *mainwin* y coordinate.
    :return: x and y screen pixel coordinates as string f'+{x}+{y}'
    """
    pos_x = mainwin.winfo_x() + mod_x
    pos_y = mainwin.winfo_y() + mod_y
    return f'+{pos_x}+{pos_y}'


def enter_only_digits(entry_string, action_type) -> bool:
    """
    Only digits are accepted and displayed in Entry field.
    Used with register() to configure Entry kw validatecommand. Example:
    myentry.configure(
        validate='key', textvariable=myvalue,
        validatecommand=(myentry.register(enter_only_digits), '%P', '%d')
        )

    :param entry_string: value entered into an Entry() widget (%P).
    :param action_type: edit action code (%d).
    :return: True or False
    """
    # Need to restrict entries to only digits,
    #   MUST use action type parameter to allow user to delete first number
    #   entered when wants to re-enter following backspace deletion.
    # source: https://stackoverflow.com/questions/4140437/
    # %P = value of the entry if the edit is allowed
    # Desired action type 1 is "insert", %d.
    if action_type == '1' and not entry_string.isdigit():
        return False
    return True


def about() -> None:
    """
    Print basic information about this module.
    """
    print(__doc__)
    print(f'{"Author:".ljust(11)}', __author__)
    print(f'{"Copyright:".ljust(11)}', __copyright__)
    print(f'{"License:".ljust(11)}', __license__)
    print(f'{"Module:".ljust(11)}', __program_name__)
    print(f'{"Version:".ljust(11)}', __version__)
    print(f'{"Dev Env:".ljust(11)}', __dev_environment__)
    print(f'{"URL:".ljust(11)}', __project_url__)
    print(f'{"Maintainer:".ljust(11)}',  __maintainer__)
    print(f'{"Status:".ljust(11)}', __status__)
    exit(0)


if __name__ == '__main__':
    about()
