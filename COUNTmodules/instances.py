#!/usr/bin/env python3

"""
Functions to determine whether another program instance is running.

Class OneWinstance(): Windows only; uses CreateMutex.
program_name(): sets the program name depending on app
exit_if_locked(): Linux and macOS only; uses fcntl.lockf()
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
__module_ver__ = '0.1.3'
__dev_environment__ = 'Python 3.8 - 3.9'
__project_url__ = 'https://github.com/csecht/CountBOINCtasks'
__maintainer__ = 'cecht'
__status__ = 'Development Status :: 4 - Beta'

import sys
from pathlib import Path
from time import sleep
from typing import TextIO

if sys.platform[:3] == 'win':
    from win32event import CreateMutex
    from win32api import CloseHandle, GetLastError
    from winerror import ERROR_ALREADY_EXISTS
elif sys.platform[:3] in 'lin, dar':
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

        :param message: The Command Prompt message to show upon
            exit.
        """
        if self.lasterror == ERROR_ALREADY_EXISTS:
            print(message)
            sleep(6)
            sys.exit(0)

    def __del__(self):
        if self.mutex:
            CloseHandle(self.mutex)


def exit_if_locked(filehandle: TextIO, message: str) -> None:
    """
    Lock a bespoke hidden file to serve as an instance sentinel for
    Linux and macOS platforms. Exit program if the file is locked.

    Example USAGE: Put this at top of if __name__ == "__main__":
        message = (f'\nNOTICE: {_program_name} is already running from'
                   f' {Path.cwd()}. Exiting...\n')
        lock_file = f'.{_program_name}_lockfile'
        filehandle = open(lock_file, 'w')
        instances.exit_if_locked(filehandle, message)

    :param filehandle: The open() text file wrapper for the lock file.
    :param message: The Terminal message to display on exit when another
        instance is running.
    """
    # Inspired by https://stackoverflow.com/questions/380870/
    #   make-sure-only-a-single-instance-of-a-program-is-running
    try:
        fcntl.lockf(filehandle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        # Linux PyInstaller stand-alone app doesn't display Terminal?
        print(message)
        sleep(6)
        sys.exit(0)


def track_sentinel() -> tuple:
    """
    Create a temporary file to serve as an instance sentinel. When the
    app closes normally, the sentinel is deleted.
    Works best on Windows systems. On Linux/macOS systems, the temp file
    may persist when the app is closed by closing the Terminal session.
    USAGE: sentinel, sentinel_count = instances.count_sentinel()
           sentinel_path = sentinel.name
           if sentinel_count > 1:
              sys.exit(
                   f'NOTICE: {_program_name} is already running from'
                   f' {Path.cwd()}. Exiting...')

    :return: the TemporaryFileWrapper object and the integer count of
        sentinel files found in the system's temporary file folder.
    """
    from tempfile import gettempdir, NamedTemporaryFile
    with NamedTemporaryFile(mode='rb', prefix=f'{program_name}_') as sentinel:
        temp_dir = gettempdir()
        sentinel_count = len(tuple(Path(temp_dir).glob(f'{program_name}_*')))
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
