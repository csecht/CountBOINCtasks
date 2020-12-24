#!/usr/bin/env python3

"""
count_now-tasks.py counts reported boinc-client tasks at set intervals.

    Copyright (C) 2020 C. Echt

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
__copyright__ = 'Copyright (C) 2020 C. Echt'
__credits__ = ['Inspired by rickslab-gpu-utils',
               'Keith Myers - Testing, debug']
__license__ = 'GNU General Public License'
__version__ = '0.4.6.2'
__program_name__ = 'count-tasks.py'
__maintainer__ = 'cecht'
__docformat__ = 'reStructuredText'
__status__ = 'Development Status :: 4 - Beta'

import argparse
import logging
import re
import statistics as stat
import subprocess
import sys
import time as t
from datetime import datetime

from COUNTmodules import boinc_command  #, count_gui2  # , count_gui

BC = boinc_command.BoincCommand()
# GUI = count_gui.CountGui()

# Here logging is lazily employed to create a file of report data.
logging.basicConfig(filename='count-tasks_log.txt', level=logging.INFO,
                    filemode="a", format='%(message)s')


def check_args(parameter) -> None:
    """
    Check command line arguments for errors.

    :param parameter: Used for the --summary parameter.
    :return: If no errors, return the parameter string.
    """

    if parameter == "0":
        msg = "Parameter value cannot be zero."
        raise argparse.ArgumentTypeError(msg)
    # Evaluate the --summary parameter, expect e.g., 15m, 2h, 1d, etc.
    if parameter != "0":
        valid_units = ['m', 'h', 'd']
        val = (parameter[:-1])
        unit = parameter[-1]
        if str(unit) not in valid_units:
            msg = f"TIME unit must be m, h, or d, not {unit}"
            raise argparse.ArgumentTypeError(msg)
        try:
            int(val)
        except ValueError as err:
            msg = "TIME must be an integer"
            raise argparse.ArgumentTypeError(msg) from err
    return parameter


def get_min(time_string: str) -> int:
    """Convert time string to minutes.

    :param time_string: format as TIMEunit, e.g., 35m, 7h, or 7d.
    :return: Time as integer minutes.
    """
    t_min = {'m': 1,
             'h': 60,
             'd': 1440}
    val = int(time_string[:-1])
    unit = time_string[-1]
    try:
        return t_min[unit] * val
    except KeyError as err:
        msg = f'Invalid time unit: {unit} -  Use: m, h, or d'
        raise KeyError(msg) from err


def fmt_sec(secs: int, fmt: str) -> str:
    """Convert seconds to the specified time format for display.

    :param secs: Time in seconds, any integer except 0.
    :param fmt: Either 'std' or 'short'
    :return: 'std' time as 00:00:00; 'short' as s, m, h, or d.
    """
    # Time conversion concept from Niko
    # https://stackoverflow.com/questions/3160699/python-progress-bar/3162864

    _m, _s = divmod(secs, 60)
    _h, _m = divmod(_m, 60)
    day, _h = divmod(_h, 24)
    msg = f"fmt_sec error: Enter secs as seconds, fmt (format) as either " \
          f" 'std' or 'short'. Arguments as entered: secs={secs}, fmt={fmt}."
    if fmt == 'short':
        if secs >= 86400:
            return f'{day:1d}d'  # option, add {h:01d}h'
        if 86400 > secs >= 3600:
            return f'{_h:01d}h'  # option, add :{m:01d}m
        if 3600 > secs >= 60:
            return f'{_m:01d}m'  # option, add :{s:01d}s
        return f'{_s:01d}s'
    if fmt == 'std':
        if secs >= 86400:
            return f'{day:1d}d {_h:02d}:{_m:02d}:{_s:02d}'
        return f'{_h:02d}:{_m:02d}:{_s:02d}'
    return msg


def intvl_timer(interval: int) -> print:
    """Provide sleep intervals and display countdown timer.

    :param interval: Minutes between task counts; range[5-60, by 5's]
    :return: A terminal/console graphic that displays time remaining.
    """
    # Idea for development from
    # https://stackoverflow.com/questions/3160699/python-progress-bar/3162864

    # Initial timer bar length; 60 fits well with most clock times.
    bar_len = 60
    prettybar = ' ' * bar_len
    # Need to assign for-loop decrement time & total sleep time as seconds.
    # Need bar segment sleep time, in sec.; is a factor of bar length.
    total_s = interval * 60
    barseg_s = round(total_s / bar_len)
    remain_s = total_s

    # \x1b[53m is DeepPink4; works on white and dark terminal backgrounds.
    whitexx_on_red = '\x1b[48;5;53;38;5;231;5m'
    whitexx_on_grn = '\x1b[48;5;28;38;5;231;5m'
    reset = '\x1b[0m'  # No color, reset to system default.
    del_line = '\x1b[2K'  # Clear entire line.

    # Needed for Windows Cmd Prompt ANSI text formatting. shell=True is safe
    # because there is no external input.
    if sys.platform[:3] == 'win':
        subprocess.call('', shell=True)

    # Not +1 in range because need only to sleep to END of interval.
    for i in range(bar_len):
        remain_bar = prettybar[i:]
        length = len(remain_bar)
        print(f"\r{del_line}{whitexx_on_red}"
              f"{fmt_sec(remain_s, 'short')}{remain_bar}"
              f"{reset}|< ~time to next count", end='')
        if length == 1:
            print(f"\r{del_line}{whitexx_on_grn}"
                  f"{fmt_sec(remain_s, 'short')}{remain_bar}"
                  f"{reset}|< ~time to next count", end='')
        remain_s = (remain_s - barseg_s)
        # Need to clear the line for data_intervals() report printing.
        if length == 0:
            print(f'\r{del_line}')
        # t.sleep(.5)  # DEBUG
        t.sleep(barseg_s)


def get_timestats(count: int, taskt: iter) -> dict:
    """
    Sum and run statistics from times, as seconds (integers or floats).

    :param count: The number of elements in taskt.
    :param taskt: A list, tuple, or set of times, in seconds.
    :return: Dict keys: tt_sum, tt_mean, tt_sd, tt_min, tt_max; values as:
    00:00:00.
    """
    total = fmt_sec(int(sum(set(taskt))), 'std')
    if count > 1:
        mean = fmt_sec(int(stat.mean(set(taskt))), 'std')
        stdev = fmt_sec(int(stat.stdev(set(taskt))), 'std')
        low = fmt_sec(int(min(taskt)), 'std')
        high = fmt_sec(int(max(taskt)), 'std')
        return {
            'tt_sum':   total,
            'tt_mean':  mean,
            'tt_sd':    stdev,
            'tt_min':   low,
            'tt_max':   high
        }
    if count == 1:
        return {
            'tt_sum':   total,
            'tt_mean':  total,
            'tt_sd':    'na',
            'tt_min':   'na',
            'tt_max':   'na'
        }

    return {
        'tt_sum':   '00:00:00',
        'tt_mean':  '00:00:00',
        'tt_sd':    'na',
        'tt_min':   'na',
        'tt_max':   'na'
        }


def main() -> None:
    """
    Main flow for count-tasks.py utility. Reports task counts and times.
    """

    # NOTE: --interval and --summary argument formats are different
    #   because summary times can be min, hr, or days, while interval times
    #   are always minutes (60m maximum).
    # NOTE: Boinc only returns tasks that were reported in past hour.
    #   Hence an --interval range limit to count tasks at least once per
    #   hour.
    parser = argparse.ArgumentParser()
    parser.add_argument('--about',
                        help='Author, copyright, and GNU license',
                        action='store_true',
                        default=False)
    parser.add_argument('--log',
                        help='Create log file of results or append to '
                             'existing log',
                        action='store_true',
                        default=False)
    # parser.add_argument('--gui',
    #                     help='Show data in graphics window.',
    #                     action='store_true',
    #                     default=False)
    parser.add_argument('--interval',
                        help='Specify minutes between task counts'
                             ' (default: %(default)d)',
                        default=60,
                        choices=range(5, 65, 5),
                        # choices=range(5),  # for testing
                        type=int,
                        metavar="M")
    parser.add_argument('--summary',
                        help='Specify time between count summaries,'
                             ' e.g., 12h, 7d (default: %(default)s)',
                        default='1d',
                        type=check_args,
                        metavar='TIMEunit')
    parser.add_argument('--count_lim',
                        help='Specify number of count reports until program'
                             ' exits (default: %(default)d)',
                        default=1008,
                        type=int,
                        metavar="N")
    args = parser.parse_args()

    count_lim = int(args.count_lim)
    interval_m = int(args.interval)
    sumry_m = get_min(args.summary)
    sumry_factor = sumry_m // interval_m
    if interval_m >= sumry_m:
        msg = "Invalid parameters: --summary time must be greater than" \
              " --interval time."
        raise ValueError(msg)

    # About me
    if args.about:
        print(__doc__)
        print('Author: ', __author__)
        print('Copyright: ', __copyright__)
        print('Credits: ', *[f'\n      {item}' for item in __credits__])
        print('License: ', __license__)
        print('Version: ', __version__)
        print('Maintainer: ', __maintainer__)
        print('Status: ', __status__)
        sys.exit(0)

    # Initial run: need to set variables for comparisons between intervals.
    # As with task names, task times as sec.microsec are unique.
    #   In future, may want to inspect task names with
    #   tnames = BC.get_reported(boincpath, 'tasks').
    time_fmt = '%Y-%b-%d %H:%M:%S'
    time_start = datetime.now().strftime(time_fmt)
    ttimes_start = BC.get_reported('elapsed time')
    ttimes_now = ttimes_start[:]
    ttimes_prev = ttimes_now[:]
    ttimes_smry = []
    count_start = len(ttimes_start)
    tic_nnt = 0  # Used to track when No New Tasks have been reported.

    # Terminal and log print formatting:
    indent = ' ' * 22
    bigindent = ' ' * 49
    del_line = '\x1b[2K'  # Clear the terminal line for a clean print.
    blue = '\x1b[1;38;5;33m'
    orng = '\x1b[1;38;5;202m'  # [32m Green3
    # grey = '\x1b[1;38;5;252m'  # Provides 'white', over-riding system default.
    undo_color = '\x1b[0m'  # Reset color to system default.
    # regex from https://stackoverflow.com/questions/14693701/
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    # Needed for Windows Cmd Prompt ANSI text formatting. shell=True is safe
    # because any command string is constructed from internal input only.
    if sys.platform[:3] == 'win':
        subprocess.call('', shell=True)

    # Report: Starting information of task times and task counts.
    tt_sum, tt_mean, tt_sd, tt_lo, tt_hi = get_timestats(count_start,
                                                         ttimes_start).values()
    report = (f'{time_start}; Number of tasks in the most recent report:'
              f' {blue}{count_start}{undo_color}\n'
              f'{indent}Counts remaining until exit: {count_lim}\n'
              f'{indent}Task Times: mean {blue}{tt_mean}{undo_color},'
              f' range [{tt_lo} - {tt_hi}],\n'
              f'{bigindent}stdev {tt_sd}, total {tt_sum}')
    # TODO: Consider repressing terminal print if --gui option used.
    print(report)
    if args.log is True:
        report = ansi_escape.sub('', report)
        logging.info("""%s; Task counter is starting with
%scount interval (minutes): %s
%ssummary interval: %s
%smax count cycles: %s
%s""",               time_start,
                     indent, args.interval,
                     indent, args.summary,
                     indent, args.count_lim,
                     report)

    # Repeated intervals: counts, time stats, and summaries.
    # Synopsis:
    # Only need to update _prev if tasks were reported in prior interval;
    #   otherwise, _prev remains as it was from earlier intervals.
    # Only need to remove previous tasks from _now when new tasks have
    #   been reported.
    # Do not include starting tasks in interval or summary counts.
    # For each interval, need to count unique tasks because some tasks
    #   may persist between counts when --interval is less than 1h.
    #   set() may not be necessary if list updates are working as intended,
    #     but better to err toward thoroughness.
    for i in range(count_lim):
        intvl_timer(interval_m)
        # t.sleep(5)  # DEBUG; or use to bypass intvl_timer.
        time_now = datetime.now().strftime(time_fmt)
        count_remain = count_lim - (i + 1)
        notrunning = False

        if len(ttimes_now) > 0:
            ttimes_prev = ttimes_now[:]

        ttimes_now = BC.get_reported('elapsed time')
        tasks_running = BC.get_tasks('active_task_state')

        if len(ttimes_now) > 0 and "EXECUTING" in tasks_running:
            ttimes_now = [task for task in ttimes_now if task not in ttimes_prev]

        # Need this check for when tasks have run out and the --get_old_tasks
        #   task times (ttimes_now) do not change between counts.
        if len(ttimes_now) > 0 and "EXECUTING" not in tasks_running:
            notrunning = True

        if len(ttimes_start) > 0:
            ttimes_now = [task for task in ttimes_now if task not in ttimes_start]
            ttimes_start.clear()

        count_now = len(set(ttimes_now))
        ttimes_smry.extend(ttimes_now)

        # Report: Repeating intervals
        # Suppress full report for no new tasks, which are expected for
        # long-running tasks (b/c 60 m is longest allowed count interval).
        # Overwrite successive NNT reports for a tidy terminal window: \x1b[2A.
        if count_now == 0:
            tic_nnt += 1
            report = (f'{time_now}; '
                      f'No tasks reported in the past {tic_nnt} {interval_m}m'
                      f' interval(s).\n'
                      f'{indent}Counts remaining until exit: {count_remain}')

            if tic_nnt == 1:
                print(f'\r{del_line}{report}')
            if tic_nnt > 1:
                print(f'\r\x1b[2A{del_line}{report}')
            if args.log is True:
                logging.info(report)
        elif count_now > 0 and notrunning is False:
            tic_nnt -= tic_nnt
            tt_sum, tt_mean, tt_sd, tt_lo, tt_hi = \
                get_timestats(count_now, ttimes_now).values()
            report = (f'{time_now}; '
                      f'Tasks reported in the past {interval_m}m:'
                      f' {blue}{count_now}{undo_color}\n'
                      f'{indent}Counts remaining until exit: {count_remain}\n'
                      f'{indent}Task Times: mean {blue}{tt_mean}{undo_color},'
                      f' range [{tt_lo} - {tt_hi}],\n'
                      f'{bigindent}stdev {tt_sd}, total {tt_sum}')

            print(f'\r{del_line}{report}')
            if args.log is True:
                report = ansi_escape.sub('', report)
                logging.info(report)
        elif notrunning is True:
            tic_nnt -= tic_nnt
            report = f'{time_now}; **Check whether any tasks are running.**\n'

            print(f'\r{del_line}{report}')
            if args.log is True:
                report = ansi_escape.sub('', report)
                logging.info(report)

        # Report: Summary intervals
        if (i + 1) % sumry_factor == 0:
            # Need unique tasks for stats and counting.
            ttimes_uniq = set(ttimes_smry)
            count_uniq = len(ttimes_uniq)

            tt_sum, tt_mean, tt_sd, tt_lo, tt_hi = \
                get_timestats(count_uniq, ttimes_uniq).values()
            report = (f'{time_now}; '
                      f'{orng}>>> SUMMARY{undo_color} count for the past'
                      f' {args.summary}: {blue}{count_uniq}{undo_color}\n'
                      f'{indent}Task Times: mean {blue}{tt_mean}{undo_color},'
                      f' range [{tt_lo} - {tt_hi}],\n'
                      f'{bigindent}stdev {tt_sd}, total {tt_sum}')
            print(f'\r{del_line}{report}')
            if args.log is True:
                report = ansi_escape.sub('', report)
                logging.info(report)

            # Need to reset data list for the next summary interval.
            ttimes_smry.clear()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.stdout.write('\n\nInterrupted by user...\n')
        logging.info(msg=f'\n{datetime.now()} --> Interrupted by user...\n')
    except OSError as error:
        sys.stdout.write(f'{error}')
        logging.info(msg=f'\n{error}\n')
