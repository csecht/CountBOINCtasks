#!/usr/bin/env python3

"""
Functions to determine whether another program instance is running.

Class OneWinstance(): Windows only; uses CreateMutex.
file_lock(): Linux and macOS only; uses fcntl.lockf()
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
__module_ver__ = '0.1.0'
__dev_environment__ = 'Python 3.8 - 3.9'
__project_url__ = 'https://github.com/csecht/CountBOINCtasks'
__maintainer__ = 'cecht'
__status__ = 'Development Status :: 4 - Beta'

import sys
from pathlib import Path
from time import sleep
from typing import TextIO

MY_OS = sys.platform[:3]

if MY_OS == 'win':
    from win32event import CreateMutex
    from win32api import CloseHandle, GetLastError
    from winerror import ERROR_ALREADY_EXISTS
elif MY_OS in 'lin, dar':
    import fcntl

# HEADSUP: This condition needs to match duplicate condition in main script.
# Use the PyInstaller stand-alone executable name as needed.
if getattr(sys, 'frozen', False):  # hasattr(sys, '_MEIPASS'):
    # Need the PyInstaller spec file EXE name= to match this program name.
    __program_name__ = 'GcountTasks'
else:
    __program_name__ = Path(sys.modules['__main__'].__file__).stem


class OneWinstance:
    """
    Limits application to single instance on Windows platforms.

    Example USAGE: Put this at top of if __name__ == "__main__":

    msg = 'The program is already running. Exiting...'
    winstance = OneWinstance()
    if winstance.already_running():
         winstance.exit_twinstance(msg)
    """
    # https://stackoverflow.com/questions/380870/
    #   make-sure-only-a-single-instance-of-a-program-is-running
    #   Modified from Pedro Lobito's post
    def __init__(self):
        # The mutex name needs to be static, suffix is meaningless.
        self.mutexname = f'{__program_name__}_ZJokEOtOTRQvOmnOylGO'
        self.mutex = CreateMutex(None, False, self.mutexname)
        self.lasterror = GetLastError()

    def already_running(self) -> bool:
        """
        Check whether program instance is currently running.

        :return: True when another instance is running.
        """
        return self.lasterror == ERROR_ALREADY_EXISTS

    @staticmethod
    def exit_twinstance(message: str) -> None:
        """
        Prevent a second instance from launching.

        :param message: The message to print upon exit.
        :return: None
        """
        # When a console displays for a PyInstaller Windows stand-alone,
        #   then need to leave console open long enough for user to
        #   read the exit message.
        print(message)
        sleep(5)
        sys.exit(0)

    def __del__(self):
        if self.mutex:
            CloseHandle(self.mutex)


def lock_or_exit(file_handle: TextIO, message: str) -> None:
    """
    Lock a bespoke hidden file to serve as an instance sentinel.
    Exit program if file is locked (another instance running).
    Only for Linux and macOS platforms.

    Example USAGE: Put this at top of if __name__ == "__main__"

    msg = 'The program is already running; Exiting...'
    lock_file = f'.{__program_name__}_lockfile'
    fh = open(lock_file, 'w')
    instances.lock_or_exit(fh, msg)

    :param file_handle: The open() text file wrapper for the lock file.
    :param message: The Terminal message to display on exit when another
        instance is running.
    """
    # Inspired by https://stackoverflow.com/questions/220525/
    #   ensure-a-single-instance-of-an-application-in-linux
    try:
        fcntl.lockf(file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print(message)
        sleep(5)
        sys.exit(0)


def track_sentinel() -> tuple:
    """
    Create a temporary file to serve as an instance sentinel. When the
    app closes normally, the sentinel is deleted.
    Works best on Windows systems. On Linux/macOS systems, the temp file
    may persist when the app is closed by closing the Terminal session.
    Example USAGE:
    sentinel, sentinel_count = instances.count_sentinel()
        sentinel_path = sentinel.name
        if sentinel_count > 1:
            sys.exit(
                'The program' is already running. Exiting...')

    :return: the TemporaryFileWrapper object and the integer count of
        sentinel files found in the system's temporary file folder.
    """
    from tempfile import gettempdir, NamedTemporaryFile
    with NamedTemporaryFile(mode='rb', prefix=f'{__program_name__}_') as sentinel:
        temp_dir = gettempdir()
        sentinel_count = len(tuple(Path(temp_dir).glob(f'{__program_name__}_*')))
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
