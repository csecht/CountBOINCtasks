#!/usr/bin/env python3

"""
Functions to determine whether another program instance is running.

Class OneWinstance(): Windows only; uses CreateMutex.
program_name(): sets the program name depending on app
exit_popup(): Create a toplevel window to announce program exit.
lock_or_exit(): Linux and macOS only; uses fcntl.lockf()
track_sentinel(): Cross-platform; uses Temporary sentinel files.

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
__module_name__ = 'instances.py'
__module_ver__ = '0.2.0'
__dev_environment__ = 'Python 3.8 - 3.9'
__project_url__ = 'https://github.com/csecht/CountBOINCtasks'
__maintainer__ = 'cecht'
__status__ = 'Development Status :: 4 - Beta'

import sys
import tkinter as tk
from pathlib import Path
from tempfile import gettempdir, NamedTemporaryFile
from time import sleep
from typing import TextIO

from COUNTmodules import binds

if sys.platform[:3] == 'win':
    from win32event import CreateMutex
    from win32api import CloseHandle, GetLastError
    from winerror import ERROR_ALREADY_EXISTS
else:
    import fcntl


def program_name() -> str:
    """
    Returns the script name or, if called from a PyInstaller stand-alone,
    the executable name. Use for setting file paths and naming windows.

    :return: Context-specific name of the main program, as string.
    """
    # Use the PyInstaller stand-alone executable name as needed.
    if getattr(sys, 'frozen', False):  # hasattr(sys, '_MEIPASS'):
        # Need the PyInstaller spec file EXE name= to match this program name.
        _program_name = 'GcountTasks'
    else:
        _program_name = Path(sys.modules['__main__'].__file__).stem
    return _program_name


class OneWinstance:
    """
    Limits program to single instance on Windows platforms.
    Example USAGE: Put this at top of if __name__ == "__main__":
        exit_msg = 'The program is already running. Exiting...'
        winstance = instances.OneWinstance()
        winstance.exit_twinstance(exit_msg)
    """
    # Inspired by https://stackoverflow.com/questions/380870/
    #   make-sure-only-a-single-instance-of-a-program-is-running
    def __init__(self):
        # The mutex name needs to be static, unique suffix is meaningless.
        self.mutexname = f'{program_name()}_ZJokEOtOTRQvOmnOylGO'
        self.mutex = CreateMutex(None, False, self.mutexname)
        self.lasterror = GetLastError()

    def already_running(self) -> bool:
        """
        No errors (ERROR_ALREADY_EXISTS == 0) when a mutex
        is first created; an error value (True) when another
        instance is created with the same mutex name.
        """
        return self.lasterror == ERROR_ALREADY_EXISTS

    # Need to leave console open long enough to read the exit message.
    def exit_twinstance(self, message: str):
        """
        Exit the program when another instance is already running.
        Delay exit after displaying *message*.

        :param message: The Command Prompt message to show upon exit.
        """
        if self.lasterror == ERROR_ALREADY_EXISTS:
            print(message)
            sleep(6)
            sys.exit(0)

    def __del__(self):
        if self.mutex:
            CloseHandle(self.mutex)


def exit_popup(message: str) -> None:
    """
    Create a tk toplevel window announcing exit from the program.
    Exit occurs when the user closes the window.

    :param message: The message to display in the exit window.
    """
    popup = tk.Tk()
    popup.title('Close window to exit')
    popup.minsize(350, 60)
    popup.configure(background='SteelBlue4')
    pos_x = popup.winfo_screenwidth() // 6
    pox_y = popup.winfo_screenheight() // 2
    popup.geometry(f'+{pos_x}+{pox_y}')

    binds.keyboard('close', popup, popup)

    tk.Label(text=message,
             font=('TkTextFont', 12),
             background='SteelBlue4',
             foreground='white',
             pady=5, padx=5).grid(ipadx=10)

    popup.mainloop()
    sys.exit(0)


def lock_or_exit(_fd: TextIO, message: str) -> None:
    """
    Lock a bespoke hidden file to serve as an instance sentinel for
    Linux and macOS platforms. Exit program if the file is locked.

    Example USAGE: Put this at top of if __name__ == "__main__":
        message = 'Program is already running. Exiting...'
        lock_file = f'.{program_name}_lockfile'
        fd = open(lock_file, 'w')
        instances.lock_or_exit(fd, message)

    :param _fd: The open() text file descriptor for the lock file.
    :param message: The message to display upon exit when another
        instance is running with the same *_fd* file descriptor.
    """
    # Inspired by https://stackoverflow.com/questions/380870/
    #   make-sure-only-a-single-instance-of-a-program-is-running
    try:
        fcntl.lockf(_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        exit_popup(message)


def track_sentinel(working_dir: Path, message=None) -> tuple:
    """
    Create a temporary file to serve as an instance sentinel. When the
    app closes, the sentinel is deleted by the system. May need to
    explicitly use sentinel.close() for certain Exceptions. Use of
    *message* triggers automatic exit if sentinel conditions are met.

    Works best on Windows systems. On Linux/macOS systems, the temp file
    may persist when the app is killed by closing the Terminal session.

    The use of the active log file's directory path as *working_dir*
    allows instances to run from different working directories without
    corrupting log data used for analysis.

    Example USAGE to prevent duplicate instances:
        sentinel, sentinel_count = instances.track_sentinel(log_path, msg)
    Example USAGE to notify about multiple instances:
        sentinel, s_count = instances.track_sentinel(log_path)
        if s_count > 1:
            print(f'{s_count} instances are running from {log_path}')
            print(f'The current instance sentinel file is {sentinel.name}')

    :param working_dir: The Path object defined by Logs.LOGFILE.parent
        in the main script.
    :param message: Display *message* and exit when another instance is
        running from the *working_dir*.
    :return: tuple of (current sentinel's TemporaryFileWrapper object,
        integer count of sentinel files with a matching prefix in the
        system's temporary file folder)
    """

    workdir = str(working_dir.resolve())

    # Need to remove problematic path characters from sentinel file name.
    trans_table = workdir.maketrans('\\/: ', '____')
    workdir_id = workdir.translate(trans_table)
    sentinel_prefix = f'sentinel_{workdir_id}_{program_name()}_'
    temp_dir = gettempdir()

    sentinel = NamedTemporaryFile(mode='rb', prefix=sentinel_prefix)

    sentinel_count = len(
        tuple(Path(temp_dir).glob(f'{sentinel_prefix}*')))

    # The first instance from a logfile dir will return variables
    #   to the main script. Subsequent instances, when this function
    #   is called with a *message*, will exit here via popup window.
    #   If not called with a *message*, then the main script can handle
    #   the returned sentinel variables as needed.
    if sentinel_count > 1 and message:
        exit_popup(message)

    return sentinel, sentinel_count


def about() -> None:
    """
    Print basic information about this module.
    """
    print(__doc__)
    print(f'{"Author:".ljust(11)}', __author__)
    print(f'{"Copyright:".ljust(11)}', __copyright__)
    print(f'{"License:".ljust(11)}', __license__)
    print(f'{"Module:".ljust(11)}', __module_name__)
    print(f'{"Module ver.:".ljust(11)}', __module_ver__)
    print(f'{"Dev Env:".ljust(11)}', __dev_environment__)
    print(f'{"URL:".ljust(11)}', __project_url__)
    print(f'{"Maintainer:".ljust(11)}',  __maintainer__)
    print(f'{"Status:".ljust(11)}', __status__)
    sys.exit(0)


if __name__ == '__main__':
    about()
