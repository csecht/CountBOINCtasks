#!/usr/bin/env python3
"""
Functions to convert, format, and analyse input time values.
Functions: string_to_m() Convert a time string to minutes.
           sec_to_format() Convert seconds to a specified time format.
           time_stat() Calculate statistical metric of a group of times.

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
__version__ = '0.2.0'
__dev_environment__ = "Python 3.8 - 3.9"
__project_url__ = 'https://github.com/csecht/CountBOINCtasks'
__maintainer__ = 'cecht'
__status__ = 'Development Status :: 4 - Beta'

import statistics
import sys
from datetime import timedelta
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


def sec_to_format(secs: int, format_type: str) -> str:
    """Convert seconds to the specified time format for display.

    :param secs: Time in seconds, any integer except 0.
    :param format_type: Either 'std', 'short', or 'clock'
    :return: 'std' time as 00:00:00; 'short' as s, m, h, or d;
             'clock' as 00:00.
    """
    # Time conversion concept from Niko
    # https://stackoverflow.com/questions/3160699/python-progress-bar/3162864
    _m, _s = divmod(secs, 60)
    _h, _m = divmod(_m, 60)
    day, _h = divmod(_h, 24)
    if format_type == 'short':
        if secs >= 86400:
            return f'{day:1d}d'  # option, add {h:01d}h'
        if 86400 > secs >= 3600:
            return f'{_h:01d}h'  # option, add :{m:01d}m
        if 3600 > secs >= 60:
            return f'{_m:01d}m'  # option, add :{s:01d}s
        return f'{_s:01d}s'
    if format_type == 'std':
        if secs >= 86400:
            return f'{day:1d}d {_h:02d}:{_m:02d}:{_s:02d}'
        return f'{_h:02d}:{_m:02d}:{_s:02d}'
    if format_type == 'clock':
        return f'{_m:02d}:{_s:02d}'
    # Error msg to developer
    return ('\nEnter secs as non-zero integer, format_type as either'
            f" 'std' or 'short'.\nArguments as entered: secs={secs}, "
            f"format_type={format_type}.\n")


def time_stat(distribution: iter, stat: str, weights=None) -> str:
    """
    Calculate statistics for group of times. Use to analyse task times
    in a file of logged interval data.

    :param distribution: List or tuple of times, as string format
                         ('00:00:00'), or as seconds (floats or integers).
    :param stat: The statistic to run: 'wtmean', 'range', 'stdev'.
                 'wtmean' requires *distribution* and *weights* parameters
                  and *distribution* times are expected to be averages.
                 'range' and 'stdev' do not use *weights*.
    :param weights: List or tuple of corresponding sample numbers
                    (integers) for each element in *distribution*. Must
                    have same number of elements as *distribution*.
                    Needed only for the 'wtmean' *stat*.
    :return: The distribution's statistic, as formatted string, '00:00:00'.
             Returns 'cannot determine' if invalid data given for 'wtmean'.
    """
    # Algorithm sources:
    # https://towardsdatascience.com/
    #   3-ways-to-compute-a-weighted-average-in-python-4e066de7a719
    # https://stackoverflow.com/questions/10663720/
    #   how-to-convert-a-time-string-to-seconds
    # https://stackoverflow.com/questions/18470627/
    #   how-do-i-remove-the-microseconds-from-a-timedelta-object

    if not stat:
        return 'missing stat param'
    if weights:
        if not all(isinstance(w, int) for w in weights):
            return 'cannot determine'
        if len(distribution) != len(weights):
            return 'cannot determine'

    # Need to convert distribution clock time strings to integer seconds, but
    #    not if distribution times are float or integer seconds.
    if all(isinstance(t, str) for t in distribution):
        dist_sec = [
            sum(x * int(t) for x, t in zip([3600, 60, 1], clk_fmt.split(":")))
            for clk_fmt in distribution]
    else:
        dist_sec = list(distribution)

    # Need to convert the timedelta clock fmt object to a string for display,
    #    and remove microseconds from the clock fmt string.
    if stat == 'wtmean':
        numerator = sum([dist_sec[i] * weights[i] for i in range(len(dist_sec))])
        denominator = sum(weights)
        return str(
            timedelta(seconds=(numerator / denominator))).split(".", 1)[0]
    if stat == 'range':
        shortest = str(timedelta(seconds=(min(dist_sec)))).split(".", 1)[0]
        longest = str(timedelta(seconds=(max(dist_sec)))).split(".", 1)[0]
        return f'[{shortest} -- {longest}]'
    if stat == 'stdev':
        return str(
            timedelta(seconds=(statistics.stdev(dist_sec)))).split(".", 1)[0]

    return 'unexpected condition'


def about() -> None:
    """
    Print details about_gui this module.
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
    sys.exit(0)


if __name__ == '__main__':
    about()