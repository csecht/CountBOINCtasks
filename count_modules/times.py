"""
Functions to convert, format, and analyse input time values.
Functions:
    string_to_min - Convert a time string to minutes.
    str2dt - Convert formatted date string to datetime.strftime()
             object.
    duration - Difference between datetime.strftime() objects.
    sec_to_format - Convert seconds to a specified time format.
    logtimes_stat - Calculate statistical metric of a group of times.
"""
# Copyright (C) 2021 C. Echt under GNU General Public License'

import statistics
from datetime import datetime, timedelta
from typing import Union


def string_to_min(time_string: str) -> Union[float, int]:
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


def str2dt(dt_str: str, str_format: str) -> datetime:
    """
    Convert formatted date string to datetime object.
    Use to compare datetimes in text files.

    :param dt_str: date and time string;
                   ex '1970-Jan-01 00:00:00'.
    :param str_format: datetime.strftime() string;
                       ex '%Y-%b-%d %H:%M:%S'.
    :return: datetime object formatted to *str_format*.
    """
    dt_obj = datetime.strptime(dt_str, str_format)
    return dt_obj


def duration(unit: str, start: datetime, end: datetime) -> float:
    """
    Difference between start and end datetime objects as the given
    time unit. Can use times.str2dt to convert formatted
    time strings to datetime objects.

    :param unit: The desired time duration unit, as a timedelta keyword:
        'weeks', 'days', 'hours', 'minutes', 'seconds', 'milliseconds',
        or 'microseconds'.
    :param start: Start time formatted datetime.strptime object.
    :param end: End time formatted datetime.strptime object. Formats of
        *start* and *end* must match.

    :return: Time difference, as float for the given *unit*.
    """

    if unit in ('weeks', 'days', 'hours', 'minutes', 'seconds',
                'microseconds', 'milliseconds'):
        return (end - start) / timedelta(**{unit: 1})
    print(f'{unit} is not a recognized datetime keyword.')
    return 0.0


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
    formatted = ''
    if format_type == 'short':
        if secs >= 86400:
            formatted = f'{day:1d}d' # option, add {h:01d}h'
        elif 86400 > secs >= 3600:
            formatted = f'{_h:01d}h' # option, add :{m:01d}m
        elif 3600 > secs >= 60:
            formatted = f'{_m:01d}m' # option, add :{s:01d}s
        else:
            formatted = f'{_s:01d}s'
    if format_type == 'std':
        if secs >= 86400:
            formatted = f'{day:1d}d {_h:02d}:{_m:02d}:{_s:02d}'
        else:
            formatted = f'{_h:02d}:{_m:02d}:{_s:02d}'
    if format_type == 'clock':
        formatted = f'{_m:02d}:{_s:02d}'

    # Error msg to developer.
    if not (isinstance(secs, int) and format_type in 'short, std, clock'):
        formatted = (
            '\nEnter secs as non-zero integer, format_type as either'
            " 'std', 'short' or 'clock'.\n"
            f"Arguments as entered: secs={secs}, format_type={format_type}.\n")

    return formatted


def logtimes_stat(distribution: iter, stat: str, weights=None) -> str:
    """
    Calculate a statistical metric for a distribution of times.
    Used to analyse times extracted from logged task times.

    :param distribution: List or tuple of times, as string format
        ('00:00:00' or '00:00'), or as seconds (floats or integers).
    :param stat: The statistic to run: 'weighted_mean', 'range', 'stdev'.
                 'weighted_mean' requires *distribution* and *weights* parameters
                  and *distribution* times are expected to be averages.
                 'range' and 'stdev' do not use *weights*.
    :param weights: List or tuple of corresponding sample numbers
                    (integers) for each element in *distribution*. Must
                    have same number of elements as *distribution*.
                    Needed only for the 'weighted_mean' *stat*.
    :return: The distribution's statistic as formatted string, '00:00:00'.
             For 'range', returns as format '[00:00:00 -- 00:00:00]'.
             Returns 'cannot determine' if invalid data given for
             'weighted_mean' or if *weights* sum to 0.
    """
    # Algorithm sources:
    # https://towardsdatascience.com/
    #   3-ways-to-compute-a-weighted-average-in-python-4e066de7a719
    # https://stackoverflow.com/questions/10663720/
    #   how-to-convert-a-time-string-to-seconds
    #   contributors thafritz and Sverrir Sigmundarson
    # https://stackoverflow.com/questions/18470627/
    #   how-do-i-remove-the-microseconds-from-a-timedelta-object
    if not stat or weights and (not all(isinstance(w, int) for w in weights)
                                or len(distribution) != len(weights)
                                or sum(weights) == 0):
        return 'cannot determine'

    # Need to convert distribution clock time strings to integer seconds, but
    #    not if distribution times are float or integer seconds.
    # Use of the reversed() function handles either 00:00:00 or 00:00 format
    def time_to_seconds(time_string):
        time_units = [1, 60, 3600]  # seconds, minutes, hours
        time_parts = map(int, reversed(time_string.split(":")))
        return sum(unit * part for unit, part in zip(time_units, time_parts))

    distrib_secs: Union[list[int], list] = [time_to_seconds(time) if isinstance(time, str)
                                           else time for time in distribution]

    def weighted_mean():
        numerator = sum(distrib_secs[i] * weights[i] for i in range(len(distrib_secs)))
        denominator = sum(weights)
        return str(timedelta(seconds=numerator / denominator)).split(".", maxsplit=1)[0]

    def time_range():
        """Do not include task times of 0:00:00 for intervals with no tasks."""
        nonzero_secs = [time for time in distrib_secs if time > 0]
        shortest = str(timedelta(seconds=min(nonzero_secs))).split(".", maxsplit=1)[0]
        longest = str(timedelta(seconds=max(nonzero_secs))).split(".", maxsplit=1)[0]
        return f'[{shortest} -- {longest}]'

    def time_stdev():
        try:
            return str(timedelta(seconds=statistics.stdev(distrib_secs))).split(".", 1)[0]
        except statistics.StatisticsError:
            return 'stdev needs more data'

    stat_functions = {
        'weighted_mean': weighted_mean,
        'range': time_range,
        'stdev': time_stdev
    }

    return stat_functions.get(stat, lambda: 'unexpected condition')()


def boinc_ttimes_stats(times_sec: iter) -> dict:
    """
    Gather statistics for a distribution of BOINC task times extracted
    from boinc-client reports. Returns dictionary strings for display
    and logging.

    :param times_sec: A list, tuple, or set of times, in seconds, as
                      integers or floats.
    :return: Dict keys: 'tt_total', 'tt_avg', 'tt_sd', 'tt_min', 'tt_max'.
             Dict values format: 00:00:00.
    """
    numtimes = len(times_sec)
    total = sec_to_format(int(sum(times_sec)), 'std')
    if numtimes > 1:
        avg = sec_to_format(int(statistics.fmean(times_sec)), 'std')
        stdev = sec_to_format(int(statistics.stdev(times_sec)), 'std')
        low = sec_to_format(int(min(times_sec)), 'std')
        high = sec_to_format(int(max(times_sec)), 'std')
    elif numtimes == 1:
        avg = stdev = low = high = total
    else:  # is 0.
        avg = stdev = low = high = total = '00:00:00'

    return {
        'taskt_total': total,
        'taskt_avg': avg,
        'taskt_sd': stdev,
        'taskt_min': low,
        'taskt_max': high}
