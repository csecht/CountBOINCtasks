#!/usr/bin/env python3
"""
Converts and formats input time values.

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
__program_name__ = 'time_convert.py'
__version__ = '0.1.2'
__maintainer__ = 'cecht'
__docformat__ = 'reStructuredText'
__status__ = 'Development Status :: 4 - Beta'

import sys
from typing import Union


def string_to_m(time_string: str) -> Union[float, int]:
    """Convert time string to minutes.

    :param time_string: format as VALUEunit, e.g., 200s, 35m, 8h, or 7d;
                        Valid units are s, m, h, or d
    :return: Time as integer minutes or as float for unit s.
    """
    t_min = {'s': 1 / 60, 'm': 1, 'h': 60, 'd': 1440}
    val = None
    unit = None
    try:
        val = int(time_string[:-1])
    except ValueError as valerr:
        err_msg = f'Invalid value unit: {val}; must be an integer.'
        raise ValueError(err_msg) from valerr
    try:
        unit = time_string[-1]
        if unit == 's':
            return round((t_min[unit] * val), 2)
        return t_min[unit] * val
    except KeyError as keyerr:
        err_msg = f'Invalid time unit: {unit} -  Use: s, m, h, or d'
        raise KeyError(err_msg) from keyerr


def sec_to_format(secs: int, time_format: str) -> str:
    """Convert seconds to the specified time format for display.

    :param secs: Time in seconds, any integer except 0.
    :param time_format: Either 'std', 'short', or 'clock'
    :return: 'std' time as 00:00:00; 'short' as s, m, h, or d;
             'clock' as 00:00.
    """
    # Time conversion concept from Niko
    # https://stackoverflow.com/questions/3160699/python-progress-bar/3162864
    _m, _s = divmod(secs, 60)
    _h, _m = divmod(_m, 60)
    day, _h = divmod(_h, 24)
    if time_format == 'short':
        if secs >= 86400:
            return f'{day:1d}d'  # option, add {h:01d}h'
        if 86400 > secs >= 3600:
            return f'{_h:01d}h'  # option, add :{m:01d}m
        if 3600 > secs >= 60:
            return f'{_m:01d}m'  # option, add :{s:01d}s
        return f'{_s:01d}s'
    if time_format == 'std':
        if secs >= 86400:
            return f'{day:1d}d {_h:02d}:{_m:02d}:{_s:02d}'
        return f'{_h:02d}:{_m:02d}:{_s:02d}'
    if time_format == 'clock':
        return f'{_m:02d}:{_s:02d}'
    # Error msg to developer
    return ('\nEnter secs as non-zero integer, time_format as either'
            f" 'std' or 'short'.\nArguments as entered: secs={secs}, "
            f"time_format={time_format}.\n")


def about() -> None:
    """
    Print details about_gui this module.
    """
    print(__doc__)
    print('Author: ', __author__)
    print('Copyright: ', __copyright__)
    print('License: ', __license__)
    print('Version: ', __version__)
    print('Maintainer: ', __maintainer__)
    print('Status: ', __status__)
    sys.exit(0)


if __name__ == '__main__':
    about()
