#!/usr/bin/env python3
"""
Methods to analyze and view BOINC task data logged to file.

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
__module_name__ = 'logs.py'
__module_ver__ = '0.1.1'
__dev_environment__ = "Python 3.8 - 3.9"
__project_url__ = 'https://github.com/csecht/CountBOINCtasks'
__maintainer__ = 'cecht'
__status__ = 'Development Status :: 4 - Beta'

import sys
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from datetime import datetime
from pathlib import Path
from re import search, findall, MULTILINE
from socket import gethostname

from COUNTmodules import binds, files, instances, times, utils

Binds = binds
Files = files
T = times
Utils = utils

__program_name__ = instances.program_name()

MY_OS = sys.platform[:3]
LONG_STRFTIME = '%Y-%b-%d %H:%M:%S'
SHORT_STRFTIME = '%Y %b %d %H:%M'
SHORTER_STRFTIME = '%b %d %H:%M'
DAY_STRFTIME = '%A %H:%M'


class Logs:
    """
    Methods to analyze and view task data logged to file.
    File paths are defined as Class attribute constants.
    """

    # Need to write log files to current working directory unless program
    #   is run from a PyInstaller frozen executable, then write to Home
    #   directory. Frozen executable paths need to be absolute paths.
    LOGFILE = Path(Path.cwd(),
                   f'{__program_name__}_log.txt').resolve()
    ANALYSISFILE = Path(Path.cwd(),
                        f'{__program_name__}_analysis.txt').resolve()

    if getattr(sys, 'frozen', False):
        LOGFILE = Path(Path.home(),
                       f'{__program_name__}_log.txt').resolve()
        ANALYSISFILE = Path(Path.home(),
                            f'{__program_name__}_analysis.txt').resolve()

    @classmethod
    def analyze_logfile(cls) -> tuple:
        """
        Reads log file and analyses Summary and Interval counts.
        Called from cls.show_analysis().

        :return: text strings to display in show_analysis() Toplevel.
        """
        sumry_dates = []
        sumry_intvl_vals = []
        num_sumry_intvl_vals = 0
        sumry_counts = []
        sumry_cnt_avg = 0.0
        sumry_cnt_range = ''

        intvl_dates = []
        intvl_vals = []
        num_intvl_vals = 0
        intvl_cnt_avg = 0.0
        intvl_cnt_range = ''
        logged_intvl_report = ''

        recent_dates = []
        recent_intvl_vals = []
        num_recent_intvl_vals = 0
        recent_counts = []
        num_recent_tasks = 0
        recent_t_wtmean = ''
        recent_intervals = True

        summary_text = ''
        recent_interval_text = ''

        try:
            logtext = Path(cls.LOGFILE).read_text()
        except FileNotFoundError:
            info = (f'On {gethostname()}, missing necessary file:\n{cls.LOGFILE}\n'
                    'Was the settings "log results" option used?\n'
                    'Was the log file deleted, moved or renamed?')
            messagebox.showerror(title='FILE NOT FOUND', detail=info)
            return summary_text, recent_interval_text  # <- Empty strings.

        # Regex is based on this structure used in CountModeler.log_it():
        # 2021-Dec-21 06:27:18; Tasks reported in the past 1h: 18
        #                       Task Time: avg 00:21:35,
        #                                  range [00:21:20 -- 00:21:54],
        #                                  stdev 00:00:11, total 06:28:45
        #                       Total tasks in queue: 53
        #                       984 counts remain.
        # 2021-Dec-21 06:27:18; >>> SUMMARY: Count for the past 1d: 402
        #                       Task Time: mean 0:21:28,
        #                                  range [00:16:03 -- 00:22:33],
        #                                  stdev 00:00:42, total 5d 23:54:05
        found_sumrys = findall(
            r'^(.*); >>> SUMMARY: .+ (\d+[mhd]): (\d+$)', logtext, MULTILINE)
        found_intvls = findall(
            r'^(.*); Tasks reported .+ (\d+[mhd]): (\d+$)', logtext, MULTILINE)
        found_intvl_avgt = findall(
            r'Tasks reported .+\n.+ avg (\d{2}:\d{2}:\d{2})', logtext, MULTILINE)
        found_intvl_t_range = findall(
            r'Tasks reported .+\n.+\n.+ range \[(\d{2}:\d{2}:\d{2}) -- (\d{2}:\d{2}:\d{2})]',
            logtext, MULTILINE)

        if found_sumrys:
            sumry_dates, sumry_intvl_vals, sumry_cnts = zip(*found_sumrys)
            num_sumry_intvl_vals = len(set(sumry_intvl_vals))
            sumry_counts = list(map(int, sumry_cnts))
            sumry_cnt_avg = round(sum(sumry_counts) / len(sumry_counts), 1)
            sumry_cnt_range = f'[{min(sumry_counts)} -- {max(sumry_counts)}]'

        if found_intvls:
            intvl_dates, intvl_vals, intvl_cnts = zip(*found_intvls)
            num_intvl_vals = len(set(intvl_vals))
            intvl_counts = list(map(int, intvl_cnts))
            num_tasks = sum(intvl_counts)
            intvl_cnt_avg = round(sum(intvl_counts) / len(intvl_counts), 1)
            intvl_cnt_range = f'[{min(intvl_counts)} -- {max(intvl_counts)}]'
            intvl_t_wtmean = T.logtimes_stat(found_intvl_avgt, 'wtmean', intvl_counts)
            intvl_t_stdev = T.logtimes_stat(found_intvl_avgt, 'stdev', intvl_counts)
            # https://www.geeksforgeeks.org/python-convert-list-of-tuples-into-list/
            # Note: using an empty tuple as a sum() starting value flattens the
            #    list of string tuples into one tuple of strings.
            intvl_t_range = T.logtimes_stat(sum(found_intvl_t_range, ()), 'range')

            # Text & data used in most count reporting conditions below:
            logged_intvl_report = (
                'Analysis of reported tasks logged from\n'
                f'{intvl_dates[0]} to {intvl_dates[-1]}\n'
                f'   {cls.uptime(logtext).ljust(11)} hours counting tasks\n'
                f'   {str(num_tasks).ljust(11)} tasks in {len(intvl_counts)} count intervals\n'
                f'   {intvl_t_wtmean.ljust(11)} weighted mean task time\n'
                f'   {intvl_t_stdev.ljust(11)} std deviation task time\n'
                f'   {intvl_t_range} range of task times\n\n')

        # Need 'recent' vars when there are interval counts following last summary.
        #   So find the list index for first interval count after the last summary.
        #   If there are no intervals after last summary, then flag and move on.
        if found_sumrys and found_intvls:
            # When there are no intervals after last summary,
            #   the last intvl date is last summary date.
            if intvl_dates[-1] == sumry_dates[-1]:
                recent_intervals = False
            else:
                index = [
                    i for i, date in enumerate(intvl_dates) if date == sumry_dates[-1]]
                index_recent = index[0] + 1  # <- The interval after the last summary.
                recent_dates, recent_intvl_vals, recent_cnts = zip(*found_intvls[index_recent:])
                num_recent_intvl_vals = len(set(recent_intvl_vals))
                recent_counts = list(map(int, recent_cnts))
                num_recent_tasks = sum(recent_counts)
                recent_t_wtmean = T.logtimes_stat(
                    found_intvl_avgt[index_recent:], 'wtmean', recent_counts)

        # Need to tailor report texts for various counting conditions.
        if not found_sumrys and not found_intvls:
            recent_interval_text = (
                f'\nAs of {datetime.now().strftime(SHORT_STRFTIME)}\n'
                '   There are not enough data to analyze.\n'
                '   Need at least one summary or one\n'
                '   interval count in the log file.\n')

        if not found_sumrys and found_intvls:
            summary_text = '\nNo summary counts are logged yet.\n\n'
            if num_intvl_vals == 1:
                recent_interval_text = (
                    f'{logged_intvl_report}'
                    f'   {str(intvl_cnt_avg).ljust(11)} tasks per {intvl_vals[0]} count interval\n'
                    f'   {intvl_cnt_range} range of task counts\n'
                )
            else:
                recent_interval_text = (
                    f'{logged_intvl_report}'
                    f'   {str(intvl_cnt_avg).ljust(11)} tasks per count interval\n'
                    f'There are {num_intvl_vals} different interval times\n'
                    f'logged, {set(intvl_vals)},\n'
                    'so interpret results with caution.\n\n'
                )

        if found_sumrys:
            if num_sumry_intvl_vals == 1:
                summary_text = (
                    f'{logged_intvl_report}'
                    'Summary data logged from:\n'
                    f'{sumry_dates[0]} to {sumry_dates[-1]}\n'
                    f'   {str(len(sumry_counts)).ljust(7)} summaries logged\n'
                    f'   {str(sumry_cnt_avg).ljust(7)}'
                    f' tasks per {sumry_intvl_vals[0]} summary interval\n'
                    f'   {sumry_cnt_range} range of task counts\n\n'
                )
            else:
                summary_text = (
                    f'{logged_intvl_report}'
                    'Summary data logged from:\n'
                    f'{sumry_dates[0]} to {sumry_dates[-1]}\n\n'
                    f'   {str(len(sumry_counts)).ljust(7)} summaries logged\n'
                    f'   {str(sumry_cnt_avg).ljust(7)} tasks per summary\n'
                    f'   {sumry_cnt_range} range of task counts\n'
                    f'There are {num_sumry_intvl_vals} different Summary interval times,\n'
                    f'   {set(sumry_intvl_vals)},\n'
                    '   so interpret results with caution.\n\n'
                )

        # Summary text has been defined, so now do recent interval text.
        if found_sumrys and found_intvls:
            if recent_intervals:
                if num_recent_intvl_vals == 1:
                    recent_interval_text = (
                        'Since last Summary, additional counts from:\n'
                        f'{recent_dates[0]} to {recent_dates[-1]}\n'
                        f'   {str(num_recent_tasks).ljust(11)} '
                        f'tasks in {len(recent_counts)} intervals of {recent_intvl_vals[0]}\n'
                        f'   {recent_t_wtmean.ljust(11)} weighted mean task time\n'
                    )
                else:
                    recent_interval_text = (
                        'Since last Summary, additional counts from:\n'
                        f'{recent_dates[0]} to {recent_dates[-1]}\n\n'
                        f'   {str(num_recent_tasks).ljust(11)} '
                        f'tasks in {len(recent_counts)} intervals of {recent_intvl_vals[0]}\n'
                        f'   {recent_t_wtmean.ljust(11)} weighted mean task time\n'
                        f'There are {num_recent_intvl_vals} different interval times,\n'
                        f'   {set(recent_intvl_vals)},\n'
                        '   so interpret results with caution.\n'
                    )
            else:
                recent_interval_text = 'No counts logged after last Summary.\n'

        return summary_text, recent_interval_text

    @classmethod
    def show_analysis(cls, mainwin) -> None:
        """
        Generate a Toplevel window to display cumulative logged task
        data that have been analyzed by cls.analyze_logfile().
        Button appends displayed results to an analysis log file.
        Called from a Logs.view() button or a master keybinding.

        :param mainwin: The main window of the tk() mainloop, e.g.,
            'root', 'main', 'app', 'self.master', etc., from which to
            identify the tk.Toplevel child that has focus.
        """

        # NOTE: When the log file is not found by analyze_logfile(), the
        #   returned texts will be empty, so no need to continue.
        summary_text, recent_interval_text = cls.analyze_logfile()
        if not summary_text and not recent_interval_text:
            return

        # Have bg match self.master_bg of the app main window.
        analysiswin = tk.Toplevel(bg='SteelBlue4')
        analysiswin.title('Analysis of logged data')
        # Need to position window over the window from which it is called.
        analysiswin.geometry(Utils.get_toplevel('position', mainwin))
        analysiswin.minsize(520, 320)

        insert_txt = summary_text + recent_interval_text

        max_line = len(max(insert_txt.splitlines(), key=len))

        # Separator dash from https://coolsymbol.com/line-symbols.html.
        # print(ord("─")) -> 9472
        #   unicodedata.name(chr(9472)) -> 'BOX DRAWINGS LIGHT HORIZONTAL'.
        # print(ord("═")) -> 9552
        #   unicodedata.name(chr(9552)) -> 'BOX DRAWINGS DOUBLE HORIZONTAL'.
        sep = f'\n{"─" * max_line}\n'

        insert_txt = insert_txt + sep

        num_lines = insert_txt.count('\n')

        analysistxt = tk.Text(analysiswin, font='TkFixedFont',
                              width=max_line, height=num_lines,
                              bg='grey100', fg='grey5',
                              relief='groove', bd=4, padx=15, pady=10)
        analysistxt.insert(1.0, insert_txt)
        analysistxt.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

        # Need to allow user to save annotated analysis text.
        def new_text():
            new_txt = analysistxt.get(1.0, tk.END)
            Files.append_txt(cls.ANALYSISFILE, new_txt, True, analysiswin)
        ttk.Button(analysiswin, text='Save analysis', command=new_text,
                   takefocus=False).pack(padx=4)

        Binds.click('right', analysistxt, mainwin)
        Binds.keyboard('close', analysiswin, mainwin)
        Binds.keyboard('append', analysiswin, None, cls.ANALYSISFILE, insert_txt)
        analysiswin.bind('<Shift-Control-A>',
                         lambda _: cls.view(cls.ANALYSISFILE, mainwin))

    @classmethod
    def uptime(cls, logtext: str) -> str:
        """
        Sum of hours spent counting tasks. Does not include time
        segments with no reported tasks counts.

        :param logtext: the full text content string from a log file.
        :return: total hours elapsed while logging data, as string.
                 Returns 'cannot determine' if negative time calculated,
                 as indication of corrupted data or user edit.
        """
        start2intvls = []
        intvl_duration = []

        # start_dt is a datetime.timedelta object, so initialize with
        #    formatted Epoch origin time.
        start_dt = T.string_to_dt('1970-Jan-01 00:00:00', LONG_STRFTIME)

        # Need to calc uptime hours for all start-to-finish segments that
        #   have interval task counts.
        # Datetimes that begin each log entry are formatted as,
        #    '2021-Dec-05 16:33:49; ...'; LONG_STRFTIME is the time
        #     format used in the log file.
        for line in logtext.split('\n'):
            if 'most recent BOINC report' in line:
                starttime_match = search(
                    r'^(.+); .+ most recent BOINC report', line).group(1)
                start_dt = T.string_to_dt(starttime_match, LONG_STRFTIME)
            if 'Tasks reported' in line:
                intvltime_match = search(
                    r'^(.+); Tasks reported', line).group(1)
                interval_dt = T.string_to_dt(intvltime_match, LONG_STRFTIME)
                start2intvls.append(T.duration('hours', start_dt, interval_dt))
                if any(hr < 0 for hr in start2intvls):
                    return 'cannot determine'

        # To calculate total interval hours, need a list of local maximums
        #    from all logged start-to-finish segments of count intervals.
        # There is no need for condition of no logged interval hours b/c
        #    this is only called from analyze_logfile() when there are hrs.
        for i, _hr in enumerate(start2intvls):
            if len(start2intvls) == 1:
                intvl_duration.append(_hr)
            elif i == 0:
                pass
            elif i < len(start2intvls) - 1:
                after = start2intvls[i + 1]
                if after < _hr:
                    intvl_duration.append(_hr)
            elif i == len(start2intvls) - 1:
                intvl_duration.append(_hr)

        return str(round(sum(intvl_duration), 1))

    @classmethod
    def view(cls, filepath: Path, mainwin) -> None:
        """
        Create a separate window to view a text file as scrolled text.
        Called from View menu bar or keybinding.

        :param filepath: A Path object of the file to view.
        :param mainwin: The main window of the tk() mainloop, e.g.,
            'root', 'main', 'app', 'self.master', etc., from which to
            identify the tk.Toplevel child that has focus.
        """
        # Need to set messages and sizes specific to OS and files.
        text_height = 30
        minsize_w = 0
        minsize_h = 0
        fnf_query = ''

        if filepath == cls.LOGFILE:
            minsize_h = 220
            # Need to set OS-specific width for font used in filetext.
            #   These widths are based on TkFixedFont:
            if MY_OS == 'lin':
                minsize_w = 800
            if MY_OS == 'win':
                minsize_w = 840
            if MY_OS == 'dar':
                minsize_w = 675
            fnf_query = 'Was the log option ticked in settings?'

        if filepath == cls.ANALYSISFILE:
            minsize_w = 510
            minsize_h = 150
            if MY_OS == 'win':
                minsize_w = 550
            fnf_query = 'Have any analysis results been saved yet?'

        if not Path.exists(filepath):
            info = (f'On {gethostname()}, file is missing:\n{filepath}\n'
                    f'{fnf_query}\n'
                    'Or, was file deleted, moved or renamed?')
            messagebox.showerror(title='FILE NOT FOUND', detail=info)
            return

        # Have bg match self.master_bg of the app main window.
        filewin = tk.Toplevel(bg='SteelBlue4',
                              highlightthickness=5,
                              highlightcolor='grey95',
                              highlightbackground='grey75'
                              )
        # Need title to include the file and local machine names.
        filewin.title(f'{filepath.parts[-1]} on {gethostname()}')
        filewin.minsize(minsize_w, minsize_h)
        filewin.focus_set()

        insert_txt = Path(filepath).read_text()

        max_line = len(max(insert_txt.splitlines(), key=len))

        # Use a "dark" background/foreground theme for file text.
        filetext = ScrolledText(filewin, font='TkFixedFont',
                                width=max_line, height=text_height,
                                bg='grey20', fg='grey80',
                                insertbackground='grey80',
                                relief='groove', bd=4, padx=12
                                )
        filetext.insert(tk.INSERT, insert_txt)
        filetext.see(tk.END)
        filetext.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

        ttk.Button(
            filewin, text='Update',
            command=lambda: Files.update(filetext, filepath, filewin),
            takefocus=False).pack(padx=4)
        ttk.Button(
            filewin, text='Backup',
            command=lambda: Files.save_as(filepath, filewin),
            takefocus=False).pack(padx=4)
        ttk.Button(
            filewin, text='File path',
            command=mainwin.filepaths,
            takefocus=False).pack(padx=4)

        if filepath == cls.LOGFILE:
            ttk.Button(filewin, text='Analysis',
                       command=lambda: cls.show_analysis(mainwin),
                       takefocus=False).pack(padx=4)
            filewin.bind('<Shift-Control-L>', lambda _: cls.show_analysis(mainwin))
            filewin.bind('<Shift-Control-A>',
                         lambda _: cls.view(cls.ANALYSISFILE, mainwin))

        if filepath == cls.ANALYSISFILE:
            filewin.geometry(Utils.get_toplevel('position', mainwin))
            ttk.Button(
                filewin, text='Erase',
                command=lambda: Files.erase(cls.ANALYSISFILE, filetext, filewin),
                takefocus=False).pack(padx=4)
            filewin.bind('<Shift-Control-L>', lambda _: cls.show_analysis(mainwin))

        Binds.click('right', filewin, mainwin)
        Binds.keyboard('close', filewin, mainwin)
        Binds.keyboard('saveas', filewin, None, filepath)


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