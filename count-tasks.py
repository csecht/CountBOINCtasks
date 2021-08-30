#!/usr/bin/env python3

"""
CountBOINCtasks provides task counts and time statistics at timed
intervals for tasks most recently reported to BOINC servers.
Download the current version from:
https://github.com/csecht/CountBOINCtasks

    Copyright (C) 2021 C. Echt

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

__author__ =    'cecht, BOINC ID: 990821'
__copyright__ = 'Copyright (C) 2021 C. Echt'
__credits__ =   ['Inspired by rickslab-gpu-utils',
                 'Keith Myers - Testing, debug']
__license__ =   'GNU General Public License'
__version__ =   '0.4.26'
__program_name__ = 'count-tasks.py'
__maintainer__ = 'cecht'
__docformat__ = 'reStructuredText'
__status__ =    'Development Status :: 4 - BETA'

import argparse
import logging
import os
import re
import statistics as stats
import sys
import time
from datetime import datetime
from pathlib import Path

from COUNTmodules import boinc_command

BC = boinc_command.BoincCommand()
# Assume log file is in the CountBOINCtasks-master folder.
LOGPATH = str(Path('count-tasks_log.txt'))
# LOGFILE = str(Path('../count-tasks_log.txt'))
# Here logging is lazily employed to manage the user file of report data.
logging.basicConfig(filename=LOGPATH, level=logging.INFO,
                    filemode="a", format='%(message)s')


class DataIntervals:
    """
    Timed interval counting, analysis, and reporting of BOINC task data.
    """

    def __init__(self):

        self.time_fmt = '%Y-%b-%d %H:%M:%S'
        self.time_start = datetime.now().strftime(self.time_fmt)
        self.time_now = None
        self.counts_remain = None
        self.num_tasks = 0
        self.report = 'None'
        self.ttimes_start = []
        self.ttimes_new = []
        self.ttimes_smry = []
        self.ttimes_uniq = []
        self.ttimes_used = [''] # Need a null string for list to be extended.
        self.count_new = None
        self.tic_nnt = 0
        self.notrunning = False

        # # Terminal and log print formatting:
        self.indent = ' ' * 22
        self.bigindent = ' ' * 33  # Indent the Task time stdev report line.
        self.del_line = '\x1b[2K'  # Clear entire terminal line for a clean print.
        self.blue = '\x1b[1;38;5;33m'
        self.orng = '\x1b[1;38;5;202m'
        self.undo_color = '\x1b[0m'  # No color, reset to system default.
        # regex from https://stackoverflow.com/questions/14693701/
        self.ansi_esc = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

        # Needed for Windows Cmd Prompt ANSI text formatting.
        if sys.platform[:3] == 'win':
            os.system("color")
            # os.system('')  # <- Alternative

        self.start_report()
        self.interval_reports()

    def start_report(self) -> None:
        """
        Upon script execution, report counts and time stats of tasks
        recently reported by BOINC.

        :returns: None; generates initial report for Terminal and log.
        """

        # As with task names, task times as sec.microsec are unique.
        #   In future, may want to inspect task names with
        #     task_names = BC.get_reported('tasks').
        self.ttimes_start = BC.get_reported('elapsed time')
        tcount_start = len(self.ttimes_start)
        # Not the most robust way to get dict values, but it's concise.
        tt_total, tt_mean, tt_sd, tt_lo, tt_hi = self.get_timestats(
            tcount_start, self.ttimes_start).values()
        self.num_tasks = len(BC.get_tasks('name'))

        if COUNT_LIM > 0:
            self.report = (
                f'{self.time_start}; Number of tasks in the most recent BOINC report:'
                f' {self.blue}{tcount_start}{self.undo_color}\n'
                f'{self.indent}Task Time: mean {self.blue}{tt_mean}{self.undo_color},'
                f' range [{tt_lo} - {tt_hi}],\n'
                f'{self.bigindent}stdev {tt_sd}, total {tt_total}\n'
                f'{self.indent}Total tasks in queue: {self.num_tasks}\n'
                f'{self.indent}Number of scheduled count intervals: {COUNT_LIM}\n'
                f'{self.indent}Counts every {INTERVAL_M}m,'
                f' summaries every {SUMMARY_T}\n'
                f'Timed intervals beginning now...\n\n')
        # Need to provide a truncated report for one-off "status" runs.
        elif COUNT_LIM == 0:
            self.report = (
                f'{self.time_start}; Number of tasks in the most recent BOINC report:'
                f' {self.blue}{tcount_start}{self.undo_color}\n'
                f'{self.indent}Task Time: mean {self.blue}{tt_mean}{self.undo_color},'
                f' range [{tt_lo} - {tt_hi}],\n'
                f'{self.bigindent}stdev {tt_sd}, total {tt_total}\n'
                f'{self.indent}Total tasks in queue: {self.num_tasks}\n')
        print(self.report)

        if args.log == 'yes':
            report_cleaned = self.ansi_esc.sub('', self.report)
            # This is proper string formatting for logging, but f-strings
            # would be fine for how "logging" is used here.
            logging.info("""%s; >>> TASK COUNTER START settings <<<
%scount interval (minutes): %s
%ssummary interval: %s
%smax count cycles: %s
%s""",
                         self.time_start,
                         self.indent, args.interval,  # same as interval_m
                         self.indent, args.summary,  # same as sumry_t
                         self.indent, args.count_lim,
                         report_cleaned)

        # Begin list of "old" or prior tasks to exclude from new tasks.
        self.ttimes_used.extend(self.ttimes_start)

    def interval_reports(self) -> None:
        """
        Gather and report task counts and time stats at timed intervals.

        :returns: None; generates reports for Terminal and log.
        """
        # Synopsis:
        # Do not include starting tasks in interval or summary counts.
        # Remove previous ("used") tasks from current ("new") task metrics.

        for loop_num in range(COUNT_LIM):
            # intvl_timer() sleeps this loop between counts.
            self.intvl_timer(INTERVAL_M)
            # time.sleep(5)  # DEBUG; or use to bypass intvl_timer.

            self.time_now = datetime.now().strftime(self.time_fmt)
            self.counts_remain = COUNT_LIM - (loop_num + 1)
            # self.tasks_total = len(BC.get_tasks('name'))

            # Do one boinccmd process call then parse tagged data from all task data
            #   (instead of calling BC.get_tasks() multiple times in succession).
            tasks_all = BC.get_tasks('all')
            # Need the literal task data tags as found in boinccmd stdout;
            #   the format is same as tag_str in BC.get_tasks().
            #   Use tuple order to populate variables based on index.
            tags = ('   name: ',
                    '   active_task_state: ',
                    '   state: ')
            self.num_tasks = len([elem for elem in tasks_all if tags[0] in elem])
            tasks_active = [elem.replace(tags[1], '') for elem in tasks_all
                            if tags[1] in elem]

            # Need a flag for when tasks have run out.
            # active_task_state for a running task is 'EXECUTING'.
            # When communication to server is stalled, all tasks will be
            #  "Ready to report" with a state of 'uploaded', so try a
            #  Project update command to prompt clearing the stalled queue.
            # tasks_active = BC.get_tasks('active_task_state')
            self.notrunning = False
            if 'EXECUTING' not in tasks_active:
                self.notrunning = True
                # task_states = BC.get_tasks('state')
                task_states = [elem.replace(tags[2], '') for elem in tasks_all
                               if tags[2] in elem]
                if 'uploaded' in task_states and 'downloaded' not in task_states:
                    local_boinc_urls = BC.get_project_url()
                    # I'm not sure how to handle multiple concurrent Projects.
                    # If they are all stalled, then updating the first works?
                    # B/c of how BC.project_action is structured, here I use the
                    #  url to get the Project name ID which is used to get the
                    #  url needed for the project cmd.  Silly, but uses
                    #  generalized methods. Is there a better way?
                    first_local_url = local_boinc_urls[0]
                    # https://stackoverflow.com/questions/8023306/get-key-by-value-in-dictionary
                    first_project = list(BC.project_url.keys())[
                        list(BC.project_url.values()).index(first_local_url)]
                    # time.sleep(1)
                    BC.project_action(first_project, 'update')
                    # Need to provide time for BOINC Project server to respond?
                    time.sleep(70)
                    report = (f'\n{self.time_now};'
                              f' *** Project update requested for {first_project}. ***\n')
                    print(report)
                    if args.log == 'yes':
                        logging.info(report)

            # Need to add all prior tasks to the "used" list. "new" task times
            #  here are carried over from the prior interval.
            self.ttimes_used.extend(self.ttimes_new)

            ttimes_sent = BC.get_reported('elapsed time')

            # Need to re-set prior ttimes_new, then repopulate it with newly
            #   reported tasks.
            self.ttimes_new.clear()
            self.ttimes_new = [task for task in ttimes_sent if task
                               not in self.ttimes_used]
            # Add new tasks to summary list for later analysis.
            # Counting a set() may not be necessary if new list works as
            #   intended, but better to err toward thoroughness and clarity.
            self.ttimes_smry.extend(self.ttimes_new)
            self.count_new = len(set(self.ttimes_new))

            # Report: Regular intervals
            # Suppress full report for no new tasks, which are expected for
            #   long-running tasks (60 m is longest allowed count interval).
            # Overwrite successive NNT reports for a tidy terminal window;
            #   move cursor up two lines before overwriting: \x1b[2A.
            # Need a notification when tasks first run out.
            if self.count_new == 0:
                self.tic_nnt += 1
                report = (f'{self.time_now}; '
                          f'{self.orng}NO TASKS reported {self.undo_color}in the past'
                          f' {self.tic_nnt} {INTERVAL_M}m interval(s).\n'
                          f'{self.counts_remain} counts remaining until exit.')
                if self.tic_nnt == 1:
                    # print(f'\r{self.del_line}{report}')
                    print(f'\x1b[1F{self.del_line}{report}')
                if self.tic_nnt > 1:
                    # print(f'\r\x1b[2A{self.del_line}{report}')
                    print(f'\x1b[2F{self.del_line}{report}')
                if args.log == 'yes':
                    report_cleaned = self.ansi_esc.sub('', report)
                    logging.info(report_cleaned)
                if self.notrunning is True:
                    report = (f'\n{self.time_now};'
                              ' *** Check whether tasks are running. ***\n')
                    print(f'\x1b[1F{self.del_line}{report}')
                    if args.log == 'yes':
                        logging.info(report)

            elif self.count_new > 0 and self.notrunning is False:
                self.tic_nnt -= self.tic_nnt
                tt_total, tt_mean, tt_sd, tt_lo, tt_hi = self.get_timestats(
                    self.count_new, self.ttimes_new).values()
                report = (
                    # f'\n{self.time_now}; Tasks reported in the past {INTERVAL_M}m:'
                    f'{self.time_now}; Tasks reported in the past {INTERVAL_M}m:'
                    f' {self.blue}{self.count_new}{self.undo_color}\n'
                    f'{self.indent}Task Time: mean {self.blue}{tt_mean}{self.undo_color},'
                    f' range [{tt_lo} - {tt_hi}],\n'
                    f'{self.bigindent}stdev {tt_sd}, total {tt_total}\n'
                    f'{self.indent}Total tasks in queue: {self.num_tasks}\n\n'
                    f'{self.counts_remain} counts remaining until exit.'
                )
                # Need to overwrite 'counts remaining' line of previous report
                #   with the timer bar, so move cursor 1 line up & delete.
                print(f'\x1b[1F{self.del_line}{report}')
                if args.log == 'yes':
                    report_cleaned = self.ansi_esc.sub('', report)
                    logging.info(report_cleaned)

            elif self.count_new > 0 and self.notrunning is True:
                report = (f'\n{self.time_now};'
                          f' *** Check whether tasks are running. ***\n')
                # print(f'\r\x1b[A{self.del_line}{report}')
                print(f'\x1b[1F{self.del_line}{report}')
                if args.log == 'yes':
                    logging.info(report)

            self.summary_reports(loop_num, self.ttimes_smry)

    def summary_reports(self, loop_num: int, ttimes_smry: list) -> None:
        """
        Report task counts & time stats summaries at timed intervals.

        :param loop_num: The for loop number from interval_reports().
        :param ttimes_smry: Cumulative list of task times from interval_reports()
        :returns: None; generates summary reports for Terminal and log.
        """

        if (loop_num + 1) % SUMRY_FACTOR == 0 and self.notrunning is False:
            # Need unique tasks for stats and counting.
            self.ttimes_uniq = set(ttimes_smry)
            count_sumry = len(self.ttimes_uniq)

            tt_total, tt_mean, tt_sd, tt_lo, tt_hi = \
                self.get_timestats(count_sumry, self.ttimes_uniq).values()
            report = (
                f'{self.time_now}; '
                f'{self.orng}>>> SUMMARY:{self.undo_color} Count for the past'
                f' {SUMMARY_T}: {self.blue}{count_sumry}{self.undo_color}\n'
                f'{self.indent}Task Time: mean {self.blue}{tt_mean}{self.undo_color},'
                f' range [{tt_lo} - {tt_hi}],\n'
                f'{self.bigindent}stdev {tt_sd}, total {tt_total}\n\n\n'
            )
            print(f'\r{self.del_line}{report}')
            if args.log == 'yes':
                report_cleaned = self.ansi_esc.sub('', report)
                logging.info(report_cleaned)

            # Need to reset data lists, in interval_reports(), for the next
            # summary interval.
            self.ttimes_smry.clear()
            self.ttimes_uniq.clear()

    @staticmethod
    def get_min(time_string: str) -> int:
        """
        Convert time string to minutes.

        :param time_string: format as TIMEunit, e.g., 35m, 7h, or 7d.
        :return: Integer minutes for any time length.
        :raises KeyError: exception for bad unit in time_string
        """
        t_min = {
            'm': 1, 'h': 60, 'd': 1440}
        val = int(time_string[:-1])
        unit = time_string[-1]
        try:
            return t_min[unit] * val
        except KeyError as err:
            err_msg = f'Invalid time unit: {unit} -  Use: m, h, or d'
            raise KeyError(err_msg) from err
        except ValueError as verr:
            err_msg = f'Invalid value unit: {val} '
            raise ValueError(err_msg) from verr

    @staticmethod
    def frmat_sec(secs: int, time_format: str) -> str:
        """
        Convert seconds to the specified time format for display.

        :param secs: Time in seconds, any integer except 0.
        :param time_format: Either 'std' or 'short'
        :return: 'std' time as 00:00:00; 'short' as s, m, h, or d.
        """
        # Time conversion concept from Niko
        # https://stackoverflow.com/questions/3160699/python-progress-bar
        # /3162864

        _m, _s = divmod(secs, 60)
        _h, _m = divmod(_m, 60)
        day, _h = divmod(_h, 24)
        note = ('fmt_sec error: Enter secs as seconds, fmt (format) as either'
                f" 'std' or 'short'. Arguments as entered: secs={secs}, "
                f"format={time_format}.")
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
        return note

    def intvl_timer(self, interval: int) -> None:
        """
        Provide sleep intervals and display countdown timer.
        Called from interval_reports().

        :param interval: Minutes between task counts; range[5-60, by 5's]
        :returns: None; generates a terminal graphic of time remaining.
        """
        # Idea for development from
        # https://stackoverflow.com/questions/3160699/python-progress-bar/3162864

        # Initial timer bar length; 60 fits well with clock times.
        bar_len = 60
        prettybar = ' ' * bar_len
        # Need bar segment sleep seconds (barseg_s) to be a factor of bar length;
        #   this sets the for-loop sleep interval and time decrement value.
        # Remaining seconds are count down from initial total seconds.
        total_s = interval * 60
        barseg_s = round(total_s / bar_len)
        remain_s = total_s

        # \x1b[53m is DeepPink4; works on white and dark terminal backgrounds.
        # 'xx' here means blinking text.
        whitexx_on_red = '\x1b[48;5;53;38;5;231;5m'
        whitexx_on_grn = '\x1b[48;5;28;38;5;231;5m'
        # reset = '\x1b[0m'  # No color, reset to system default.
        # del_line = '\x1b[2K'  # Clear entire line.

        # Not +1 in range because need only to sleep to END of interval.
        # When range ends, sleep segments end and interval_reports() continues
        #   with the rest of its for-loop statements.
        for i in range(bar_len):
            remain_bar = prettybar[i:]
            num_segments = len(remain_bar)
            print(f"\r{self.del_line}{whitexx_on_red}"
                  f"{self.frmat_sec(remain_s, 'short')}{remain_bar}"
                  f"{self.undo_color}|< ~time to next count", end='')
            if num_segments == 1:
                print(f"\r{self.del_line}{whitexx_on_grn}"
                      f"{self.frmat_sec(remain_s, 'short')}{remain_bar}"
                      f"{self.undo_color}|< ~time to next count", end='')
            remain_s = (remain_s - barseg_s)
            # Need to clear the progress bar line for a clean report print.
            if num_segments == 0:
                # print(f'\r\x1b[A{del_line}')
                print(f'\r{self.del_line}')

            # t.sleep(.5)  # DEBUG
            time.sleep(barseg_s)

    def get_timestats(self, numtasks: int, tasktimes: iter) -> dict:
        """
        Sum and run statistics from times, as sec (integers or floats).

        :param numtasks: The number of elements in tasktimes.
        :param tasktimes: A list, tuple, or set of times, in seconds.
        :return: Dict keys: tt_total, tt_mean, tt_sd, tt_min, tt_max.
                 Dict values as: 00:00:00.
        """
        total = self.frmat_sec(int(sum(set(tasktimes))), 'std')
        if numtasks > 1:
            mean = self.frmat_sec(int(stats.mean(set(tasktimes))), 'std')
            stdev = self.frmat_sec(int(stats.stdev(set(tasktimes))), 'std')
            low = self.frmat_sec(int(min(tasktimes)), 'std')
            high = self.frmat_sec(int(max(tasktimes)), 'std')
            return {
                'tt_total': total,
                'tt_mean': mean,
                'tt_sd': stdev,
                'tt_min': low,
                'tt_max': high}
        if numtasks == 1:
            return {
                'tt_total': total,
                'tt_mean': total,
                'tt_sd': 'na',
                'tt_min': 'na',
                'tt_max': 'na'}

        return {
            'tt_total': '00:00:00',
            'tt_mean': '00:00:00',
            'tt_sd': 'na',
            'tt_min': 'na',
            'tt_max': 'na'}


def check_summary_arg(parameter: str) -> str:
    """
    Check --summary command line arguments for errors.

    :param parameter: Passed from parser.add_argument 'type' call.
    :return: If no errors, then return the parameter string.
    :raises ValueError: exception for bad value in parameter
    """
    # This is used ONLY for the --summary argument. Where is best placement?
    if parameter == "0":
        instruct = "Parameter value cannot be zero."
        raise argparse.ArgumentTypeError(instruct)
    # Evaluate the --summary parameter, expect e.g., 15m, 2h, 1d, etc.
    if parameter != "0":
        valid_units = ['m', 'h', 'd']
        val = (parameter[:-1])
        unit = parameter[-1]
        if str(unit) not in valid_units:
            instruct = f"TIME unit must be m, h, or d, not {unit}"
            raise argparse.ArgumentTypeError(instruct)
        try:
            int(val)
        except ValueError as err:
            err_msg = "TIME must be an integer"
            raise argparse.ArgumentTypeError(err_msg) from err
    return parameter


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    # NOTE: --interval and --summary argument formats are different
    #   because summary times can be min, hr, or days, while interval times
    #   are always minutes (60 maximum).
    # NOTE: Boinc only returns tasks that were reported in past hour.
    #   Hence an --interval maximum limit to count tasks at least once per
    #   hour.
    parser = argparse.ArgumentParser()
    parser.add_argument('--about',
                        help='Author, copyright, and GNU license',
                        action='store_true',
                        default=False)
    parser.add_argument('--log',
                        help='Create log file of results or append to '
                             'existing log'
                             ' (default: %(default)s)',
                        default='yes',
                        choices=['yes', 'no'])
    # parser.add_argument('--gui',
    #                     help='Show data in interactive graphics window.',
    #                     action='store_true',
    #                     default=True)
    parser.add_argument('--interval',
                        help='Specify minutes between task counts'
                             ' (default: %(default)d)',
                        default=60,
                        # default=1,  # For testing
                        choices=range(5, 65, 5),
                        type=int,
                        metavar="M")
    parser.add_argument('--summary',
                        help='Specify time between count summaries,'
                             ' e.g., 12h, 7d (default: %(default)s)',
                        default='1d',
                        type=check_summary_arg,
                        metavar='TIMEunit')
    parser.add_argument('--count_lim',
                        help='Specify number of count reports until program'
                             ' exits (default: %(default)d);'
                             ' 0 provides current data',
                        default=1008,
                        type=int,
                        metavar="N")
    args = parser.parse_args()

    # Variables to manage parser arguments.
    COUNT_LIM = int(args.count_lim)
    INTERVAL_M = int(args.interval)
    SUMMARY_T = str(args.summary)
    summary_m = DataIntervals.get_min(SUMMARY_T)
    SUMRY_FACTOR = summary_m // INTERVAL_M
    # Variables used for CountGui() data display.
    # intvl_str = f'{args.interval}m'
    # sumry_intvl = args.summary  # in CountGUI(), refactor to sumry_t

    if INTERVAL_M >= summary_m:
        info = ("Invalid parameters: --summary time must be greater than",
                " --interval time.")
        raise ValueError(info)

    if args.about:
        print(__doc__)
        print('Author:    ', __author__)
        print('Copyright: ', __copyright__)
        print('Credits:   ', *[f'\n      {item}' for item in __credits__])
        print('License:   ', __license__)
        print('Version:   ', __version__)
        print('Maintainer:', __maintainer__)
        print('Status:    ', __status__)
        sys.exit(0)

    try:
        DataIntervals()
    except KeyboardInterrupt:
        # For aesthetics, move cursor to beginning of timer line and erase line.
        exit_msg = (f'\r\x1b[K\n\n  *** Interrupted by user ***\n'
                    f'  Quitting now...{datetime.now()}\n\n')
        sys.stdout.write(exit_msg)
        # Need to remove formatting from log text.
        exit_cleaned = exit_msg.replace('\r\x1b[K\n', '')
        logging.info(msg=exit_cleaned)
    # TODO: Consider this? https://dev.to/xowap/the-ultimate-python-main-18kn
