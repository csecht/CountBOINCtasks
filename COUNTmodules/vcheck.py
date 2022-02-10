#!/usr/bin/env python3
"""
Simple check of current Python version.
Functions:
minversion() - Exit program if not minimum required version.
maxversion() - Warn if newer than tested versions.

    Copyright (C) 2020  C. Echt

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
__copyright__ = 'Copyright (C) 2021 C. Echt'
__license__ = 'GNU General Public License'
__module_name__ = 'vcheck.py'
__module_ver__ = '0.1.2'
__dev_environment__ = "Python 3.8 - 3.9"
__project_url__ = 'https://github.com/csecht/CountBOINCtasks'
__maintainer__ = 'cecht'
__status__ = 'Development Status :: 4 - Beta'

import sys


def minversion(req_version: str) -> None:
    """
    Check current Python version against minimum version required.
    Exit program if current version is less than required.

    :param req_version: The required minimum major and minor version;
        example, '3.6'.
    """
    ver = tuple(map(int, req_version.split('.')))
    if sys.version_info < ver:
        print(f'Sorry, but this program requires Python {req_version} or later.\n'
              'Current Python version:'
              f' {sys.version_info.major}.{sys.version_info.minor}\n'
              'Python downloads are available from https://docs.python.org/')
        sys.exit(0)


def maxversion(req_version: str) -> None:
    """
    Check current Python version against maximum version required.
    Issue warning if current version is more than *req_version*.

    :param req_version: The required maximum major and minor version;
        example, '3.9'.
    """
    ver = tuple(map(int, req_version.split('.')))
    if sys.version_info > ver:
        print(f'NOTICE: this program has not yet been tested with'
              f' Python versions newer than {req_version}.\n'
              'Current Python version:'
              f' {sys.version_info.major}.{sys.version_info.minor}\n')


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
