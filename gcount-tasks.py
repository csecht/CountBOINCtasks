#!/usr/bin/env python3

"""
CountBOINCtasks provides task counts and time statistics at timed
intervals for tasks most recently reported to BOINC servers. This is
a tkinter-based GUI version of count-tasks.py using a MVC architecture;
inspiration: Brian Oakley; https://stackoverflow.com/questions/32864610/

    Copyright (C) 2021 C. Echt

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see https://www.gnu.org/licenses/.
"""
# ^^ Info for --about invocation argument or __doc__>>
__author__ = 'cecht, BOINC ID: 990821'
__copyright__ = 'Copyright (C) 2021 C. Echt'
__credits__ = ['Inspired by rickslab-gpu-utils']
__license__ = 'GNU General Public License'
__version__ = '0.1.5'
__program_name__ = 'gcount-tasks.py'
__project_url__ = 'https://github.com/csecht/CountBOINCtasks'
__maintainer__ = 'cecht'
__docformat__ = 'reStructuredText'
__status__ = 'Development Status :: 2 - Beta'

import logging
import random
import shutil
import signal
import statistics as stats
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from COUNTmodules import boinc_command

try:
    import tkinter as tk
    import tkinter.font
    from tkinter import messagebox, ttk
    from tkinter.scrolledtext import ScrolledText
except (ImportError, ModuleNotFoundError) as error:
    print('gcount_tasks.py requires tkinter, which is included with some\n'
          'Python 3.7+distributions.\n'
          'Install the most recent version or re-install Python and include Tk/Tcl.\n'
          'Python downloads are available from python.org\n'
          'On Linux-Ubuntu you may need: sudo apt install python3-tk\n'
          f'See also: https://tkdocs.com/tutorial/install.html \n{error}')

if sys.version_info < (3, 7):
    print('Program requires Python 3.7 or later.')
    sys.exit(1)
MY_OS = sys.platform[:3]
# MY_OS = 'win'  # TESTING
TIME_FORMAT = '%Y-%b-%d %H:%M:%S'
BC = boinc_command.BoincCommand()
# Log file should be in the CountBOINCtasks-master folder.
# LOGFILE = Path('../count-tasks_log.txt')
LOGFILE = Path('count-tasks_log.txt')
CWD = Path.cwd()
BKUPFILE = 'count-tasks_log(copy).txt'
# GUI_TITLE = __file__  # <- for development
GUI_TITLE = 'BOINC task counter'

# Here logging is lazily employed to manage the file of report data.
logging.basicConfig(filename=str(LOGFILE), level=logging.INFO, filemode="a",
                    format='%(message)s')

# Use this for a clean exit from Terminal; bypasses __name__ KeyInterrupt msg.
signal.signal(signal.SIGINT, signal.SIG_DFL)


# The engine that gets BOINC data and runs timed data counts.
class CountModeler:
    """
    Counting, stat analysis, and formatting of BOINC task data.
    """

    def __init__(self, share):
        self.share = share

        self.th_lock = threading.Lock()

        self.ttimes_smry = []
        self.count_new = None
        self.tic_nnt = 0
        self.notrunning = False
        self.proj_stalled = False
        self.report_summary = False

        # Log file print formatting:
        self.indent = ' ' * 22
        self.bigindent = ' ' * 33

    def default_settings(self) -> None:
        """Set or reset default run parameters in the setting dictionary.
        """

        self.share.setting['interval_t'].set('60m')
        self.share.setting['interval_m'].set(60)
        self.share.setting['summary_t'].set('1d')
        self.share.setting['sumry_t_value'].set(1)
        self.share.setting['sumry_t_unit'].set('day')
        self.share.setting['cycles_max'].set(1008)
        self.share.setting['do_log'].set(1)

    def set_start_data(self):
        """
        Gather initial data of tasks and their times; set data dict
        stringvars.
        """
        # As with task names, task times as sec.microsec are unique.
        #   In future, may want to inspect task names with
        #     task_names = BC.get_reported('tasks').
        ttimes_start = BC.get_reported('elapsed time')
        # Begin list used/old tasks to exclude from new tasks; list is used
        #   in set_interval_data() to track tasks across intervals.
        self.share.ttimes_used.extend(ttimes_start)
        self.share.data['task_count'].set(len(ttimes_start))

        # num_tasks_all Label config and grid are defined in Viewer __init__:
        #  set value here for use in display_data()
        self.share.data['num_tasks_all'].set(len(BC.get_tasks('name')))

        # Need to parse data returned from get_ttime_stats().
        startdict = self.get_ttime_stats(
            self.share.data['task_count'].get(), ttimes_start)
        tt_mean = startdict['tt_mean']
        tt_max = startdict['tt_max']
        tt_min = startdict['tt_min']
        tt_sd = startdict['tt_sd']
        tt_total = startdict['tt_total']
        tt_range = f'{tt_min} -- {tt_max}'

        self.share.data['tt_mean'].set(tt_mean)
        self.share.data['tt_sd'].set(tt_sd)
        self.share.data['tt_range'].set(tt_range)
        self.share.data['tt_total'].set(tt_total)

    def set_interval_data(self) -> None:
        """
        Update and evaluate data for task status and times, set
        data dict and notice stringvars. Run interval timer.
        Display regular and summary interval data.
        Called as Thread from V.display_data() so that other tkinter
        widgets can be used during interval sleep time.
        Calls: get_ttime_stats(), get_minutes(), notify_and_log().
        """
        ttimes_new = []
        cycles_max = self.share.setting['cycles_max'].get()
        interval_m = self.share.setting['interval_m'].get()
        # tstart = time.perf_counter()  # TESTING
        for cycle in range(cycles_max):
            if cycle == 1:
                # Need to change button name and function from Start to Interval
                #   after initial cycle[0] completes and intvl data displays.
                #  It might be better if statement were in Viewer, but simpler
                #  to put it here with easy reference to cycle.
                self.share.start_b.grid_remove()
                self.share.intvl_b.grid(row=0, column=1,
                                        padx=(16, 0), pady=(8, 4))

            # Need to sleep between counts and also display a countdown timer.
            # interval_sec = 1  # DEBUG/TESTING
            # Limit total time of interval to actual time (Epoch seconds) b/c
            # each sleep cycle runs a little longer than target interval.
            interval_sec = interval_m * 60
            target_sec = interval_m * 60.0
            clock_begin = time.time()
            for _sec in range(interval_sec):
                if cycle == cycles_max:
                    break
                clock_curr = time.time()
                if clock_curr > (clock_begin + target_sec):
                    self.share.data['time_next_cnt'].set('00:00')
                    break
                interval_sec -= 1
                _m, _s = divmod(interval_sec, 60)
                _h, _m = divmod(_m, 60)
                time_remain = f'{_m:02d}:{_s:02d}'
                self.share.data['time_next_cnt'].set(time_remain)
                time.sleep(1.0)

            cycles_remain = int(self.share.data['cycles_remain'].get()) - 1
            self.share.data['cycles_remain'].set(cycles_remain)

            # Best to show weekday with time.
            self.share.data['time_prev_cnt'].set(
                datetime.now().strftime('%A %H:%M:%S'))

            # Do one boinccmd call then parse tagged data from all
            # task data, instead of multiple BC.get_tasks() calls.
            tasks_all = BC.get_tasks('all')
            # Need the literal task data tags as found in boinccmd stdout;
            #   the format are same as tag_str in BC.get_tasks().
            #   Use tuple index to populate variables.
            tags = ('   name: ',
                    '   active_task_state: ',
                    '   state: ')
            num_tasks_all = len([elem for elem in tasks_all if tags[0] in elem])
            self.share.data['num_tasks_all'].set(num_tasks_all)
            tasks_active = [elem.replace(tags[1], '') for elem in tasks_all
                            if tags[1] in elem]

            # Need to reset flags for when tasks have run out and
            #   project has stalled.
            # When communication to server is stalled, all tasks will be
            #  "Ready to report" with a state of 'uploaded', so force a
            #   Project update to prompt clearing the stalled upload.
            self.notrunning = False
            self.proj_stalled = False
            if 'EXECUTING' not in tasks_active:
                self.notrunning = True
                task_states = [elem.replace(tags[2], '') for elem in tasks_all
                               if tags[2] in elem]
                if 'uploaded' in task_states and 'downloaded' not in task_states:
                    self.proj_stalled = True
                    local_boinc_urls = BC.get_project_url()
                    # I'm not sure how to handle multiple concurrent Projects.
                    # If they are all stalled, then updating the first works?
                    # B/c of how BC.project_action is structured, here I use the
                    #  url to get the Project name ID which is used to get the
                    #  url needed for the project cmd.  Silly, but uses
                    #  generalized methods. Is there a better way?
                    first_local_url = local_boinc_urls[0]
                    self.share.first_project = list(BC.project_url.keys())[
                        list(BC.project_url.values()).index(first_local_url)]
                    BC.project_action(self.share.first_project, 'update')
                    # Need to provide time for BOINC Project server to respond?
                    # The long sleep needs to suspend set_interval_data() thread;
                    #  use threading.Lock() to suspend timer for sleep duration.(?)
                    with self.th_lock:
                        time.sleep(70)

            # NOTE: Starting tasks are not included in interval and summary
            #   counts, but starting task times are used here to evaluate
            #   "new" tasks.
            # Need to add all prior tasks to the "used" list.
            #  "new" task times are carried over from the prior interval;
            #  For cycle[0], ttimes_used was set in set_start_data().
            self.share.ttimes_used.extend(ttimes_new)
            ttimes_reported = BC.get_reported('elapsed time')

            # Need to re-set prior ttimes_new, then repopulate it with newly
            #   reported tasks.
            ttimes_new.clear()
            ttimes_new = [task for task in ttimes_reported if task
                          not in self.share.ttimes_used]

            # Counting a set() may not be necessary if new list works as
            #   intended, but better to err toward thoroughness and clarity.
            task_count_new = len(set(ttimes_new))
            self.share.data['task_count'].set(task_count_new)
            # Add new tasks to summary list for later analysis.
            self.ttimes_smry.extend(ttimes_new)

            # Record when no new tasks were reported in past interval;
            #   Needed in notify_and_log().
            if task_count_new == 0:
                self.tic_nnt += 1
            elif task_count_new > 0 and not self.notrunning:
                self.tic_nnt = 0
            # Need to robustly parse data returned from get_ttime_stats().
            intervaldict = self.get_ttime_stats(task_count_new, ttimes_new)
            tt_mean = intervaldict['tt_mean']
            tt_max = intervaldict['tt_max']
            tt_min = intervaldict['tt_min']
            tt_sd = intervaldict['tt_sd']
            tt_range = f'{tt_min} -- {tt_max}'
            tt_total = intervaldict['tt_total']

            self.share.data['tt_mean'].set(tt_mean)
            self.share.data['tt_sd'].set(tt_sd)
            self.share.data['tt_range'].set(tt_range)
            self.share.data['tt_total'].set(tt_total)

            # SUMMARY DATA ####################################################
            # NOTE: Starting data are not included in summary tabulations.
            summary_m = self.get_minutes(self.share.setting['summary_t'].get())
            interval_m = int(self.share.setting['interval_t'].get()[:-1])
            summary_factor = summary_m // interval_m
            if (cycle + 1) % summary_factor == 0 and self.notrunning is False:
                # Flag used in notify_and_log() for logging.
                self.report_summary = True
                # Need to activate disabled Summary data button now; only need
                #  statement for 1st summary, but, oh well, here we go again...
                self.share.sumry_b.config(state=tk.NORMAL)

                # Need unique tasks for stats and counting.
                ttimes_uniq = set(self.ttimes_smry)
                task_count_sumry = len(ttimes_uniq)
                self.share.data['task_count_sumry'].set(task_count_sumry)

                summarydict = self.get_ttime_stats(task_count_sumry, ttimes_uniq)
                tt_mean = summarydict['tt_mean']
                tt_max = summarydict['tt_max']
                tt_min = summarydict['tt_min']
                tt_sd = summarydict['tt_sd']
                tt_range = f'{tt_min} -- {tt_max}'
                tt_total = summarydict['tt_total']

                self.share.data['tt_mean_sumry'].set(tt_mean)
                self.share.data['tt_sd_sumry'].set(tt_sd)
                self.share.data['tt_range_sumry'].set(tt_range)
                self.share.data['tt_total_sumry'].set(tt_total)

                # Need to reset data list for the next summary interval.
                self.ttimes_smry.clear()

            self.notify_and_log()

    def notify_and_log(self) -> None:
        """
        Display interval and summary metrics for recently reported BOINC
        task data.
        Provide notices for aberrant task status. Optional log to file.
        Called from set_interval_data().
        """

        # Post notices for task or BOINC status that might need user attention.
        # NOTE: Values for notrunning, proj_stalled and tic_nnt are set and
        # reset in set_interval_data(); proj_stalled is True when tasks
        # neither running or "downloaded" and all are "uploaded";
        #   b/c forcing a Project update may prompt the server to action.
        # The notice_l grid overlays the complement_txt grid.

        cycles_max = self.share.setting['cycles_max'].get()

        if self.notrunning and self.proj_stalled:
            self.share.notice_txt.set(
                'PROJECT UPDATE REQUESTED; see log file.\n'
                '(Ctrl_Shift-C clears notice.)')
            self.share.compliment_txt.grid_remove()  # Necessary?
            self.share.notice_l.grid(row=13, column=1, columnspan=2,
                                     padx=5, pady=5, sticky=tk.W)
            app.update_idletasks()
        elif not self.notrunning and self.tic_nnt > 0:
            self.share.notice_txt.set(
                f'NO TASKS reported in past {self.tic_nnt} count(s).\n'
                '(Ctrl_Shift-C clears notice.)')
            self.share.compliment_txt.grid_remove()  # Necessary?
            self.share.notice_l.grid(row=13, column=1, columnspan=2,
                                     padx=5, pady=5, sticky=tk.W)
            app.update_idletasks()
        elif self.notrunning:
            self.share.notice_txt.set(
                'NO TASKS WERE RUNNING; check BOINC Manager\n'
                '(Ctrl_Shift-C clears notice.)')
            # Notice grids in compliment_me spot; initial grid implementation
            self.share.compliment_txt.grid_remove()  # Necessary?
            self.share.notice_l.grid(row=13, column=1, columnspan=2,
                                     padx=5, pady=5, sticky=tk.W)
            app.update_idletasks()
        # When things are normal, notice_txt will be removed on next interval.
        else:
            self.share.notice_l.grid_remove()  # Necessary?

        if self.share.data['cycles_remain'].get() == 0:
            eoc_time = datetime.now().strftime(TIME_FORMAT)
            self.share.notice_txt.set(
                f'{cycles_max} counts completed {eoc_time}')
            self.share.compliment_txt.grid_remove()  # Necessary?
            self.share.notice_l.grid(row=13, column=1, columnspan=2,
                                     padx=5, pady=5, sticky=tk.W)

        # Need to log regular intervals for the do_log option
        if self.share.setting['do_log'].get() == 1:
            time_now = datetime.now().strftime(TIME_FORMAT)
            interval_t = self.share.setting['interval_t'].get()
            task_count_new = self.share.data['task_count'].get()
            tt_mean = self.share.data['tt_mean'].get()
            tt_sd = self.share.data['tt_sd'].get()
            tt_range = self.share.data['tt_range'].get()
            tt_total = self.share.data['tt_total'].get()
            num_tasks_all = self.share.data['num_tasks_all'].get()
            cycles_remain = self.share.data['cycles_remain'].get()

            summary_t = self.share.setting['summary_t'].get()
            tcount_sum = self.share.data['task_count_sumry'].get()
            ttmean_sum = self.share.data['tt_mean_sumry'].get()
            ttsd_sum = self.share.data['tt_sd_sumry'].get()
            ttrange_sum = self.share.data['tt_range_sumry'].get()
            tttotal_sum = self.share.data['tt_total_sumry'].get()

            if self.notrunning:
                report = (f'\n{time_now};'
                          ' *** NO TASKS RUNNING. Check BOINC Manager.***\n')
                logging.info(report)

                time_now = datetime.now().strftime(TIME_FORMAT)
                if self.proj_stalled:
                    report = (
                        f'\n{time_now};'
                        f' *** PROJECT UPDATE REQUESTED for {self.share.first_project}. ***\n'
                        'All tasks were in uploaded status and waiting to upload.\n'
                        'Following a forced Project update they should now be uploaded f.\n'
                        'Check BOINC Manager.')
                    logging.info(report)

            if self.tic_nnt > 0:
                report = (f'{time_now}: NO TASKS reported in the past'
                          f' {self.tic_nnt} interval(s).\n'
                          f'{cycles_remain} counts remaining until exit.')
                logging.info(report)

            # This should be same as: task_count_new > 0 and
            #   self.share.notrunning is False; that is, everything normal.
            elif self.tic_nnt == 0:
                report = (
                    f'\n{time_now}; Tasks reported in the past {interval_t}:'
                    f' {task_count_new}\n'
                    f'{self.indent}Task Time: mean {tt_mean}, range [{tt_range}],\n'
                    f'{self.bigindent}stdev {tt_sd}, total {tt_total}\n'
                    f'{self.indent}Total tasks in queue: {num_tasks_all}\n'
                    f'{self.indent}{cycles_remain} counts remaining until exit.'
                )
                logging.info(report)

            if self.report_summary:
                report = (
                    f'\n{time_now}; >>> SUMMARY: Count for the past'
                    f' {summary_t}: {tcount_sum}\n'
                    f'{self.indent}Task Time: mean {ttmean_sum}, range [{ttrange_sum}],\n'
                    f'{self.bigindent}stdev {ttsd_sum}, total {tttotal_sum}\n'
                )
                logging.info(report)
                # Need to reset flag to toggle summary logging.
                self.report_summary = False

            if self.share.data['cycles_remain'].get() == 0:
                report = f'\n### {cycles_max} counting cycles have ended. ###\n'
                logging.info(report)

    @staticmethod
    def get_minutes(time_string: str) -> int:
        """Convert time string to minutes.

        :param time_string: format as TIMEunit, e.g., 35m, 7h, or 7d;
                            Valid units are m, h, or d.
        :return: Time as integer minutes.
        """
        t_min = {'m': 1, 'h': 60, 'd': 1440}
        val = int(time_string[:-1])
        unit = time_string[-1]
        try:
            return t_min[unit] * val
        # Error msgs to developer
        except KeyError as kerr:
            err_msg = f'Invalid time unit: {unit} -  Use: m, h, or d'
            raise KeyError(err_msg) from kerr
        except ValueError as verr:
            err_msg = f'Invalid value unit: {val} '
            raise ValueError(err_msg) from verr

    @staticmethod
    def format_sec(secs: int, time_format: str) -> str:
        """Convert seconds to the specified time format for display.

        :param secs: Time in seconds, any integer except 0.
        :param time_format: Either 'std' or 'short'
        :return: 'std' time as 00:00:00; 'short' as s, m, h, or d.
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
        # Error msg to developer
        return ('\nEnter secs as integer, time_format as either'
                f" 'std' or 'short'.\nArguments as entered: secs={secs}, "
                f"time_format={time_format}.\n")

    def get_ttime_stats(self, numtasks: int, tasktimes: iter) -> dict:
        """
        Sum and run statistics from times, as sec (integers or floats).

        :param numtasks: The number of elements in tasktimes.
        :param tasktimes: A list, tuple, or set of times, in seconds.
        :return: Dict keys: tt_total, tt_mean, tt_sd, tt_min, tt_max;
                 Dict values as: 00:00:00.
        """
        total = self.format_sec(int(sum(set(tasktimes))), 'std')
        if numtasks > 1:
            mean = self.format_sec(int(stats.mean(set(tasktimes))), 'std')
            stdev = self.format_sec(int(stats.stdev(set(tasktimes))), 'std')
            low = self.format_sec(int(min(tasktimes)), 'std')
            high = self.format_sec(int(max(tasktimes)), 'std')
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
        # numtasks are 0...
        return {
            'tt_total': '00:00:00',
            'tt_mean': '00:00:00',
            'tt_sd': 'na',
            'tt_min': 'na',
            'tt_max': 'na'}

    # Not the most logical place for this method, but it works well here when
    #   need to write exit message to the log file.
    def quit_gui(self, event=None) -> None:
        """
        Safe and informative exit from the program.
        Called from multiple widgets via Controller.quitgui().

        :param event: Needed for keybindings.
        :type event: Direct call from keybindings.
        """
        time_now = datetime.now().strftime(TIME_FORMAT)
        quit_msg = f'\n{time_now}: *** User has quit the program. ***\n Exiting...\n'
        print(quit_msg)
        if self.share.setting['do_log'].get() == 1:
            logging.info(quit_msg)
        app.destroy()
        sys.exit(0)


# The tkinter GUI engine that runs as main thread.
class CountViewer(tk.Frame):
    """
    The Viewer communicates with Modeler via 'share' objects handled
    through the Controller class. All GUI widgets go here.
    """
    print('gcount-tasks now running...')

    def __init__(self, master, share):
        super().__init__(master)
        self.share = share
        self.dataframe = tk.Frame()

        # Set colors for row labels and data display.
        # http://www.science.smith.edu/dftwiki/index.php/Color_Charts_for_TKinter
        self.row_fg = 'LightCyan2'  # foreground for row labels
        self.data_bg = 'grey40'  # background for data labels and frame
        self.master_bg = 'SkyBlue4'  # also used for row header labels.
        self.notice_fg = 'khaki'
        # Label foreground configuration vars.
        self.emphasize = 'grey90'
        self.highlight = 'gold'
        self.deemphasize = 'grey60'

        # Log text formatting vars:
        self.report = 'none'
        self.indent = ' ' * 22
        self.bigindent = ' ' * 33

        # Basic run parameters/settings passed between Viewer and Modeler.
        # Defaults, from in Modeler.default_settings, can be changed in
        # settings().
        self.share.setting = {
            'interval_t': tk.StringVar(),
            'interval_m': tk.IntVar(),
            'sumry_t_value': tk.IntVar(),
            'sumry_t_unit': tk.StringVar(),
            'summary_t': tk.StringVar(),
            'cycles_max': tk.IntVar(),
            'do_log': tk.IntVar()
        }

        # Common data var for display; passed between Viewer and Modeler
        self.share.data = {
            # Start and Interval data
            'task_count': tk.IntVar(),
            'tt_mean': tk.StringVar(),
            'tt_sd': tk.StringVar(),
            'tt_range': tk.StringVar(),
            'tt_total': tk.StringVar(),
            # General data
            'time_prev_cnt': tk.StringVar(),
            'cycles_remain': tk.IntVar(),
            'time_next_cnt': tk.StringVar(),
            'num_tasks_all': tk.IntVar(),
            # Summary data
            'task_count_sumry': tk.IntVar(),
            'tt_mean_sumry': tk.StringVar(),
            'tt_sd_sumry': tk.StringVar(),
            'tt_range_sumry': tk.StringVar(),
            'tt_total_sumry': tk.StringVar(),
        }

        # Used in set_start_data() and set_interval_data()
        self.share.ttimes_used = ['']

        # Used in notify_and_log()
        self.share.notice_txt = tk.StringVar()

        # settings() toplevel window widgets:
        self.settings_win = tk.Toplevel(relief='raised', bd=3)
        self.sumry_t_value = ttk.Entry(self.settings_win)
        self.sumry_t_unit = ttk.Combobox(self.settings_win)
        self.cycles_max_entry = ttk.Entry(self.settings_win)
        self.showdata_button = ttk.Button(self.settings_win)

        # Master window widgets:
        # Set interval & summary focus button attributes here b/c need to
        #   configure them in different modules.
        # start_b will be replaced with ttk intvl_b after first interval
        # completes; it is re-grid in set_interval_data().
        # start_b is tk.B b/c that accepts disabledforeground keyword.
        # TODO: Check whether MacOS recognizes tk activebackground)
        # TODO: Work up OS-specific button widths.
        self.share.start_b = tk.Button(text='Starting data', width=18,
                                       disabledforeground='grey10',
                                       state=tk.DISABLED)
        self.share.intvl_b = ttk.Button(text='Interval data', width=18,
                                        command=self.emphasize_intvl_data)
        self.share.sumry_b = ttk.Button(text='Summary data', width=20,
                                        command=self.emphasize_sumry_data)

        # Labels for settings values in master window; configure in display_data():
        self.time_start_l = tk.Label(self.dataframe, text='Waiting to start...',
                                     bg=self.data_bg, fg='grey90')
        self.interval_t_l = tk.Label(self.dataframe, width=20, borderwidth=2,
                                     textvariable=self.share.setting['interval_t'],
                                     relief='groove', bg=self.data_bg)
        self.summary_t_l = tk.Label(self.dataframe, width=20, borderwidth=2,
                                    textvariable=self.share.setting['summary_t'],
                                    relief='groove', bg=self.data_bg)
        self.cycles_max_l = tk.Label(textvariable=self.share.setting['cycles_max'],
                                     bg=self.master_bg, fg=self.row_fg)

        # Labels for BOINC data; gridded in their respective show_methods().
        self.task_count_l = tk.Label(self.dataframe, width=3, bg=self.data_bg,
                                     textvariable=self.share.data['task_count'])
        self.tt_mean_l = tk.Label(self.dataframe, width=3, bg=self.data_bg,
                                  textvariable=self.share.data['tt_mean'])
        self.tt_sd_l = tk.Label(self.dataframe, width=3, bg=self.data_bg,
                                textvariable=self.share.data['tt_sd'])
        self.tt_range_l = tk.Label(self.dataframe, width=3, bg=self.data_bg,
                                   textvariable=self.share.data['tt_range'])
        self.tt_total_l = tk.Label(self.dataframe, width=3, bg=self.data_bg,
                                   textvariable=self.share.data['tt_total'])
        self.task_count_sumry_l = tk.Label(self.dataframe, width=3, bg=self.data_bg,
                                           textvariable=self.share.data['task_count_sumry'])
        self.ttmean_sumry_l = tk.Label(self.dataframe, width=3, bg=self.data_bg,
                                       textvariable=self.share.data['tt_mean_sumry'])
        self.ttsd_sumry_l = tk.Label(self.dataframe, width=3, bg=self.data_bg,
                                     textvariable=self.share.data['tt_sd_sumry'])
        self.ttrange_sumry_l = tk.Label(self.dataframe, width=3, bg=self.data_bg,
                                        textvariable=self.share.data['tt_range_sumry'])
        self.ttsum_sumry_l = tk.Label(self.dataframe, width=3, bg=self.data_bg,
                                      textvariable=self.share.data['tt_total_sumry'])
        self.time_prev_cnt_l = tk.Label(
            textvariable=self.share.data['time_prev_cnt'],
            bg=self.master_bg, fg=self.row_fg)
        self.time_next_cnt_l = tk.Label(
            textvariable=self.share.data['time_next_cnt'],
            bg=self.master_bg, fg=self.notice_fg)
        self.cycles_remain_l = tk.Label(
            textvariable=self.share.data['cycles_remain'],
            bg=self.master_bg, fg=self.row_fg)
        self.num_tasks_all_l = tk.Label(
            textvariable=self.share.data['num_tasks_all'],
            bg=self.master_bg, fg=self.row_fg)
        # Text for compliment_txt is configured in compliment_me()
        self.share.compliment_txt = tk.Label(
            fg=self.notice_fg, bg=self.master_bg,
            relief='flat', border=0)
        # Notice label will share grid with complement_txt to display notices.
        self.share.notice_l = tk.Label(
            textvariable=self.share.notice_txt,
            fg=self.notice_fg, bg=self.master_bg, relief='flat', border=0)

        self.config_master()
        self.master_widgets()
        # Need to set window position here (not in config_master),so it doesn't
        #    shift when PassModeler.config_results() is called b/c different
        #    from app position.
        # self.master.geometry('+96+134')  # or app.geometry('+96+134')

    def config_master(self) -> None:
        """
        Master frame configuration, keybindings, frames, and row headers.
        """
        # Background color of container Frame is configured in __init__
        # OS-specific window size ranges set in Controller __init__
        # self.master.minsize(466, 365)
        self.master.title(GUI_TITLE)
        # Need to color in all of master Frame, and use light grey border;
        #    changes to near white for click-drag.
        self.master.configure(bg=self.master_bg,
                              highlightthickness=3,
                              highlightcolor='grey75',
                              highlightbackground='grey95')

        # Theme controls entire window theme, but only for ttk.Style objects.
        # Options: classic, alt, clam, default, aqua(MacOS only)
        ttk.Style().theme_use('alt')

        # Set up universal and OS-specific keybindings and menus
        self.master.bind_all('<Escape>', self.share.quitgui)
        cmdkey = ''
        if MY_OS in 'lin, win':
            cmdkey = 'Control'
        elif MY_OS == 'dar':
            cmdkey = 'Command'
        self.master.bind(f'<{f"{cmdkey}"}-q>', self.share.quitgui)
        self.master.bind('<Shift-Control-C>', self.share.complimentme)
        self.master.bind("<Control-l>", lambda q: self.show_log())

        # Make data rows and columns stretch with window drag size.
        # Don't vertically stretch separator rows.
        rows2config = (2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13)
        for _r in rows2config:
            self.master.columnconfigure(1, weight=1)
        self.master.columnconfigure(2, weight=1)

        # Set up frame to display data. Putting frame here instead of in
        # master_widgets gives proper alignment of row headers and data.
        self.dataframe.configure(borderwidth=3, relief='sunken',
                                 bg=self.data_bg)
        self.dataframe.grid(row=2, column=1, rowspan=7, columnspan=2,
                            padx=(5, 10), sticky=tk.NSEW)
        framerows = (2, 3, 4, 5, 6, 7, 8)
        for row in framerows:
            self.dataframe.rowconfigure(row, weight=1)

        self.dataframe.columnconfigure(1, weight=1)
        self.dataframe.columnconfigure(2, weight=1)

        # Fill in headers for data rows.
        row_header = {'Counting since': 2,
                      'Count interval': 3,
                      '# tasks reported': 4,
                      'Task times:  mean': 5,
                      'stdev': 6,
                      'range': 7,
                      'total': 8,
                      'Time of last count:': 10,
                      'Next count in:': 11,
                      # 'Counts remaining:': 11,
                      'Tasks in queue:': 12,
                      'Notices:': 13
                      }
        for header, rownum in row_header.items():
            tk.Label(self.master, text=f'{header}',
                     bg=self.master_bg, fg=self.row_fg
                     ).grid(row=rownum, column=0, padx=(5, 0), sticky=tk.E)
        # Need to accommodate two headers in same row.
        tk.Label(self.master, text='Counts remaining:',
                 bg=self.master_bg, fg=self.row_fg
                 ).grid(row=11, column=2, sticky=tk.W)

    def master_widgets(self) -> None:
        """
        Master frame menus, buttons, and separators.
        """

        # creating a menu instance
        menu = tk.Menu(self.master)
        self.master.config(menu=menu)

        # Add pull-down menus
        os_accelerator = ''
        if MY_OS in 'lin, win':
            os_accelerator = 'Ctrl'
        elif MY_OS == 'dar':
            os_accelerator = 'Command'
        file = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="File", menu=file)
        file.add_command(label="Backup log file", command=self.backup_log)
        # Update note: settings() is only run upon startup.
        # file.add_command(label='Settings...', command=self.settings)
        file.add_separator()
        file.add_command(label='Quit', command=self.share.quitgui,
                         # MacOS doesn't display this accelerator
                         #   b/c can't override MacOS native Command+Q;
                         #   and don't want Ctrl+Q displayed or used.
                         accelerator=f'{os_accelerator}+Q')

        view = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="View", menu=view)
        view.add_command(label="Log file", command=self.show_log,
                         # MacOS: can't display Cmd+L b/c won't override native cmd.
                         accelerator="Ctrl+L")
        help_menu = tk.Menu(menu, tearoff=0)
        info = tk.Menu(self.master, tearoff=0)
        menu.add_cascade(label="Help", menu=help_menu)
        help_menu.add_cascade(label='Info...', menu=info)
        info.add_command(label='- Interval and Summary data buttons'
                               ' switch visual emphasis...')
        info.add_command(label='    ...those buttons activate once their data post.')
        info.add_command(label='- Number of "Tasks in queue" updates every interval.')
        info.add_command(label='- Review count and notice history with "View log".')
        info.add_command(label='- "Backup log file" places a copy in your Home folder.')

        help_menu.add_command(label="Compliment", command=self.share.complimentme,
                              accelerator="Ctrl+Shift+C")
        help_menu.add_command(label="About", command=self.share.about)

        # Create or configure button widgets:
        style_button = ttk.Style(self.master)
        style_button.configure('TButton', background='grey80', anchor='center')
        # NOTE: Start, Interval, & Summary button attributes are in __init__.
        viewlog_b = ttk.Button(text='View log file', command=self.show_log)
        # quit_b = ttk.Button(text='Quit', command=self.share.quitgui)

        # For colored separators, use ttk.Frame instead of ttk.Separator.
        # Initialize then configure style for separator color.
        style_sep = ttk.Style(self.master)
        style_sep.configure('TFrame', background=self.master_bg)
        sep1 = ttk.Frame(relief="raised", height=6)
        sep2 = ttk.Frame(relief="raised", height=6)

        # %%%%%%%%%%%%%%%%%%% grid: sorted by row number %%%%%%%%%%%%%%%%%%%%%%
        # viewlog_b.grid(row=0, column=0, padx=5, pady=5)
        viewlog_b.grid(row=0, column=0, padx=5, pady=(8, 4))
        self.share.start_b.grid(row=0, column=1, padx=(16, 0), pady=(6, 4))
        self.share.sumry_b.grid(row=0, column=2, padx=(0, 22), pady=(8, 4))
        sep1.grid(row=1, column=0, columnspan=5, padx=5, pady=(2, 5), sticky=tk.EW)
        # Intervening rows are gridded in display_data()
        sep2.grid(row=9, column=0, columnspan=5, padx=5, pady=(6, 6), sticky=tk.EW)
        # quit_b.grid(row=13, column=2, padx=(0, 5), pady=(4, 0), sticky=tk.E)
        # compliment_txt grids in "Notices": row, same position as notices_txt_l.
        self.share.compliment_txt.grid(row=13, column=1, columnspan=2,
                                       padx=5, pady=5, sticky=tk.W)

        # Need if condition so startup sequence isn't recalled when subsequent
        #  Viewer methods are called; interval_t will be set, so
        #  starting sequence will be skipped. Starting sequence:
        #  default_settings(), settings(), check_and_set(),
        #  settings.check_show_close(), V.display_data() -> M.set_start_data() &
        #  intvl_thread for M.set_interval_data().
        # ^^^ There must be a cleaner way to structure start functions?
        if not self.share.setting['interval_t'].get():
            self.share.defaultsettings()
            self.settings()

    def settings(self) -> None:
        """
        A Toplevel window called from master_widgets() at startup.
        Use to confirm default parameters or set new ones for count and
        summary interval times, counting limit, and log file option.
        """
        # Toplevel window basics
        # Need self. b/c window parent is used for a messagebox in check_and_set().
        self.settings_win.title('First, set run parameters')
        if MY_OS in 'lin, win':
            self.settings_win.attributes('-topmost', True)
        # In macOS, topmost places Combobox selections BEHIND the window.
        #    So allow app window to remain topmost and offset settings_win
        elif MY_OS == 'dar':
            # self.settings_win.focus()
            self.settings_win.geometry('+640+134')
        self.settings_win.resizable(False, False)

        # Colors should match those of master/parent window.
        settings_fg = 'LightCyan2'
        settings_bg = 'SkyBlue4'
        self.settings_win.configure(bg=settings_bg)
        style = ttk.Style()
        style.configure('TLabel', background=settings_bg, foreground=settings_fg)

        intvl_choice = ttk.Combobox(self.settings_win)
        log_choice = tk.Checkbutton(self.settings_win)

        # Need to disable default window Exit; only allow exit from active Confirm button.
        # https://stackoverflow.com/questions/22738412/a-suitable-do-nothing-lambda-expression-in-python
        #    to just disable 'X' exit, the protocol func can be lambda: None, or type(None)()
        def no_exit_on_x():
            msg = ('Please exit window with "Return" button.\n'
                   '"Return" is allowed once "Confirm" is clicked.')
            messagebox.showinfo(title='Confirm before closing', detail=msg,
                                parent=self.settings_win)

        self.settings_win.protocol('WM_DELETE_WINDOW', no_exit_on_x)

        # Functions for Combobox selections.
        def set_intvl_selection(*args):
            self.share.setting['interval_t'].set(intvl_choice.get())

        def set_sumry_unit(*args):
            self.share.setting['sumry_t_unit'].set(self.sumry_t_unit.get())

        # Need to restrict entries to only digits,
        #   MUST use action type parameter to allow user to delete first number
        #   entered when wants to re-enter following backspace deletion.
        def test_dig_entry(entry_string, action_type):
            """
            Only digits are accepted and displayed in Entry field.
            Used with .register() to configure Entry kw validatecommand.
            """
            # source: https://stackoverflow.com/questions/4140437/
            if action_type == '1':  # action type 1 is "insert"
                if not entry_string.isdigit():
                    return False
            return True

        def explain_zero_max():
            max_label = ttk.Label(self.settings_win, foreground='orange',
                                  text='Enter 0 for a 1-off count.')
            max_label.grid(column=0, columnspan=3, row=4,
                           padx=10, pady=(0, 5), sticky=tk.E)

        def check_show_close():
            """
            Calls check_and_set(), activates or disables interval cycles,
            closes settings window, and calls display_data().
            Called from showdata_button.
            """
            # Need a final check in case something changes since initial
            #   check_and_set().
            self.check_and_set()

            if self.share.setting['cycles_max'].get() == 0:
                self.share.data['cycles_remain'].set(0)
                self.share.setting['interval_t'].set('DISABLED')
                self.share.setting['summary_t'].set('DISABLED')
                self.share.notice_txt.set(
                    'STATUS REPORT ONLY. (Ctrl_Shift-C clears notice.)')
                # compliment_txt grids in same position; initial grid implementation
                self.share.notice_l.grid(row=13, column=1, columnspan=2,
                                         pady=5, sticky=tk.W)
                self.display_data()
                self.settings_win.destroy()
            else:
                self.display_data()
                self.settings_win.destroy()

        # Have user select interval times for counting and summary cycles.
        intvl_choice.configure(state='readonly', width=4, height=12,
                               textvariable=self.share.setting['interval_t'])

        intvl_choice['values'] = ('60m', '55m', '50m', '45m', '40m', '35m',
                                  '30m', '25m', '20m', '15m', '10m', '5m')
        intvl_choice.bind("<<ComboboxSelected>>", set_intvl_selection)

        intvl_label1 = ttk.Label(self.settings_win, text='Count interval')
        intvl_label2 = ttk.Label(self.settings_win, text='minutes')

        self.sumry_t_value.configure(
            validate='key', width=4,
            textvariable=self.share.setting['sumry_t_value'],
            validatecommand=(
                self.sumry_t_value.register(test_dig_entry), '%P', '%d'))

        self.sumry_t_unit.configure(state='readonly',
                                    textvariable=self.share.setting['sumry_t_unit'],
                                    values=('day', 'hr', 'min'), width=4)
        self.sumry_t_unit.bind("<<ComboboxSelected>>", set_sumry_unit)

        sumry_label1 = ttk.Label(self.settings_win, text='Summary interval: time value')
        sumry_label2 = ttk.Label(self.settings_win, text='time unit')

        # Specify number limit of counting cycles to run before program exits.
        self.cycles_max_entry.configure(
            validate='key', width=4,
            textvariable=self.share.setting['cycles_max'],
            validatecommand=(
                self.cycles_max_entry.register(test_dig_entry), '%P', '%d'))

        cycles_label1 = ttk.Label(self.settings_win, text='# Count cycles')
        # cycles_label2 = ttk.Label(self.settings_win, text='default 1008')

        cycles_query_button = ttk.Button(self.settings_win, text='?', width=0,
                                         command=explain_zero_max)

        # Need a user option to log results to file.
        # 'do_log' value is BooleanVar() & kw "variable" automatically sets it.
        log_choice.configure(variable=self.share.setting['do_log'],
                             bg=settings_bg, borderwidth=0)
        log_label = ttk.Label(self.settings_win, text='Log results to file')

        confirm_button = ttk.Button(self.settings_win, text='Confirm',
                                    command=self.check_and_set)

        # Default button should display all default values in real time.
        default_button = ttk.Button(self.settings_win, text='Use defaults',
                                    command=self.share.defaultsettings)

        self.showdata_button.configure(text='Count now',
                                       command=check_show_close)
        # Need to disable button to force user to first "Confirm" settings,
        #    even when using default settings: it is a 2-click closing.
        #    'Show data' button is enabled (tk.NORMAL) in check_and_set().
        self.showdata_button.config(state=tk.DISABLED)

        # Grid all window widgets; sorted by row.
        intvl_choice.grid(column=1, row=0)
        intvl_label1.grid(column=0, row=0, padx=5, pady=10, sticky=tk.E)
        intvl_label2.grid(column=2, row=0, padx=5, pady=10, sticky=tk.W)
        sumry_label1.grid(column=0, row=1, padx=(10, 5), pady=10, sticky=tk.E)
        self.sumry_t_value.grid(column=1, row=1)
        sumry_label2.grid(column=2, row=1, padx=5, pady=10, sticky=tk.E)
        self.sumry_t_unit.grid(column=3, row=1, padx=5, pady=10, sticky=tk.W)
        if MY_OS == 'lin':
            cycles_query_button.grid(column=0, row=2, padx=(80, 0), sticky=tk.W)
        if MY_OS == 'win':
            cycles_query_button.grid(column=0, row=2, padx=(60, 0), sticky=tk.W)
        cycles_label1.grid(column=0, row=2, padx=5, pady=10, sticky=tk.E)
        self.cycles_max_entry.grid(column=1, row=2)
        # cycles_label2.grid(column=2, row=2, padx=5, pady=10, sticky=tk.W)
        log_label.grid(column=0, row=3, padx=5, pady=10, sticky=tk.E)
        log_choice.grid(column=1, row=3, padx=0, sticky=tk.W)
        confirm_button.grid(column=3, row=3, padx=10, pady=10, sticky=tk.E)
        default_button.grid(column=0, row=4, padx=10, pady=(0, 5), sticky=tk.W)
        self.showdata_button.grid(column=3, row=4, padx=10, pady=(0, 5), sticky=tk.E)

    def check_and_set(self):
        """
        Confirm that summary time > interval time, set all settings
        from settings() to their textvariable dict values, and log to
        file if optioned. Called from settings.close_and_show() via
        Confirm button.
        """
        self.showdata_button.config(state=tk.DISABLED)

        # Note: self.share.setting['interval_t'] is set in settings().
        interval_m = int(self.share.setting['interval_t'].get()[:-1])
        self.share.setting['interval_m'].set(interval_m)
        # interval_m = self.share.setting['interval_m'].get()

        sumry_value = self.sumry_t_value.get()
        self.share.setting['sumry_t_value'].set(sumry_value)
        # if sumry_value == 0 then it is caught by interval_m comparison.
        if not sumry_value:
            self.share.setting['sumry_t_value'].set(1)
        elif sumry_value != '0':
            self.share.setting['sumry_t_value'].set(int(sumry_value.lstrip('0')))

        # Need to set summary_t here as concat of two sumry_t_ element strings,
        #   then convert to minutes to use in comparisons.
        summary_t = f"{self.share.setting['sumry_t_value'].get()}{self.sumry_t_unit.get()[:1]}"
        self.share.setting['summary_t'].set(summary_t)
        summary_m = int(self.share.getminutes(summary_t))
        if interval_m >= summary_m:
            self.showdata_button.config(state=tk.DISABLED)
            info = "Summary time must be greater than interval time"
            messagebox.showerror(title='Invalid entry', detail=info,
                                 parent=self.settings_win)
        elif interval_m < summary_m:
            self.showdata_button.config(state=tk.NORMAL)

        # Need to remove leading zeros, but allow a zero entry.
        #   Replace empty Entry with default values.
        cycles_max = self.cycles_max_entry.get()
        if cycles_max == '':
            self.share.setting['cycles_max'].set(1008)
        elif cycles_max != '0':
            self.share.setting['cycles_max'].set(int(cycles_max.lstrip('0')))
        # Allow zero entry for 1-off status report of task data.
        elif cycles_max == '0':
            self.share.setting['cycles_max'].set(0)
        # Need to set initial cycles_remain to cycles_max b/c
        #   is decremented in notify_and_log() to track cycle number.
        self.share.data['cycles_remain'].set(
            self.share.setting['cycles_max'].get())

    def display_data(self) -> None:
        """
        Config and grid data labels in master window; display start data.
        Log data to file if optioned. Show default settings and task
        metrics for the most recent BOINC report.
        Called from settings.check_close_show() with 'Show data' button.
        """
        time_start = datetime.now().strftime(TIME_FORMAT)
        self.share.setstartdata()

        # Thread is started here b/c this method is called only once.
        # There are no thread.join(), so use daemon.
        if self.share.setting['cycles_max'].get() > 0:
            self.share.intvl_thread = threading.Thread(
                target=self.share.setintervaldata, daemon=True)
            self.share.intvl_thread.start()

        # Need to keep sumry_b button disabled until after 1st summary interval.
        self.share.sumry_b.config(state=tk.DISABLED)

        # Need self.share... whenever var is used in other MVC classes.
        self.time_start_l.config(text=time_start)
        self.share.data['time_prev_cnt'].set(
            'The most recent BOINC report when program started')
        self.interval_t_l.config(foreground=self.emphasize)
        self.summary_t_l.config(foreground=self.deemphasize)
        self.task_count_l.config(foreground=self.highlight)
        # count_next Label is config __init__ and set in set_interval_time().
        # num_tasks_all Label is config __init__ and set in set_start_data().
        # TODO: ^^ Consider having num_tasks_all update more frequently
        #  than interval_t; every 5 min? Work into countdown clock?

        # Starting count data and times (from past boinc-client hour).
        # Textvariables are configured in __init__; their values
        #   (along with self.share.tt_range) are set in set_start_data()
        #    and called via Controller setstartdata().
        self.tt_mean_l.configure(foreground=self.highlight)
        self.tt_sd_l.configure(foreground=self.emphasize)
        self.tt_range_l.configure(foreground=self.emphasize)
        self.tt_total_l.configure(foreground=self.emphasize)

        self.task_count_sumry_l.configure(foreground=self.deemphasize)
        self.ttmean_sumry_l.configure(foreground=self.deemphasize)
        self.ttsd_sumry_l.configure(foreground=self.deemphasize)
        self.ttrange_sumry_l.configure(foreground=self.deemphasize)
        self.ttsum_sumry_l.configure(foreground=self.deemphasize)

        # TODO: Suss why window height increases a few pixels when these are
        #  gridded vs. initial (pre-settings()) blank no-data display.
        #  It causes an obnoxious jump in frame/window size
        # Initial gridding of data labels, start & intervals; sorted by row.
        self.time_start_l.grid(row=2, column=1, padx=(10, 16), sticky=tk.EW,
                               columnspan=2)
        self.interval_t_l.grid(row=3, column=1, padx=(12, 6), sticky=tk.EW)
        self.summary_t_l.grid(row=3, column=2, padx=(0, 16), sticky=tk.EW)
        self.task_count_l.grid(row=4, column=1, padx=10, sticky=tk.EW)
        self.tt_mean_l.grid(row=5, column=1, padx=10, sticky=tk.EW)
        self.tt_sd_l.grid(row=6, column=1, padx=10, sticky=tk.EW)
        self.tt_range_l.grid(row=7, column=1, padx=10, sticky=tk.EW)
        self.tt_total_l.grid(row=8, column=1, padx=10, sticky=tk.EW)
        self.time_prev_cnt_l.grid(row=10, column=1, padx=3, sticky=tk.W,
                                  columnspan=2)
        self.time_next_cnt_l.grid(row=11, column=1, padx=3, sticky=tk.W)
        # Place cycles_remain value in same cell as its header, but shifted right,
        #  b/c if instead grid in column=3, then new column added to right of dataframe.
        self.cycles_remain_l.grid(row=11, column=2, padx=(125, 0), sticky=tk.W)
        self.num_tasks_all_l.grid(row=12, column=1, padx=3, sticky=tk.W)

        self.task_count_sumry_l.grid(row=4, column=2, padx=(0, 16), sticky=tk.EW)
        self.ttmean_sumry_l.grid(row=5, column=2, padx=(0, 16), sticky=tk.EW)
        self.ttsd_sumry_l.grid(row=6, column=2, padx=(0, 16), sticky=tk.EW)
        self.ttrange_sumry_l.grid(row=7, column=2, padx=(0, 16), sticky=tk.EW)
        self.ttsum_sumry_l.grid(row=8, column=2, padx=(0, 16), sticky=tk.EW)

        if self.share.setting['do_log'].get() == 1:
            interval_t = self.share.setting['interval_t'].get()
            summary_t = self.share.setting['summary_t'].get()
            tcount_start = self.share.data['task_count'].get()
            tt_mean = self.share.data['tt_mean'].get()
            tt_sd = self.share.data['tt_sd'].get()
            tt_range = self.share.data['tt_range'].get()
            tt_total = self.share.data['tt_total'].get()
            num_tasks_all = self.share.data['num_tasks_all'].get()
            cycles_max = self.share.setting['cycles_max'].get()
            if cycles_max > 0:
                self.report = (
                    '\n>>> TASK COUNTER START settings <<<\n'
                    f'{time_start}; Number of tasks in the most recent BOINC report:'
                    f' {tcount_start}\n'
                    f'{self.indent}Task Time: mean {tt_mean},'
                    f' range [{tt_range}],\n'
                    f'{self.bigindent}stdev {tt_sd}, total {tt_total}\n'
                    f'{self.indent}Total tasks in queue: {num_tasks_all}\n'
                    f'{self.indent}Number of scheduled count intervals: {cycles_max}\n'
                    f'{self.indent}Counts every {interval_t},'
                    f' summaries every {summary_t}\n'
                    f'Timed intervals beginning now...\n')
            # Need to provide a truncated report for one-off "status" runs.
            elif cycles_max == 0:
                self.report = (
                    f'\n{time_start}; STATUS REPORT\n'
                    f'{self.indent}Number of tasks in the most recent BOINC report:'
                    f' {tcount_start}\n'
                    f'{self.indent}Task Time: mean {tt_mean},'
                    f' range [{tt_range}],\n'
                    f'{self.bigindent}stdev {tt_sd}, total {tt_total}\n'
                    f'{self.indent}Total tasks in queue: {num_tasks_all}\n')
        logging.info(self.report)

    # Methods for buttons, menu items, keybinds.
    def emphasize_intvl_data(self) -> None:
        """
        Switches font emphasis from Summary data to Interval data.
        Called from 'Interval data' button.
        """

        self.interval_t_l.config(foreground=self.emphasize)
        self.summary_t_l.config(foreground=self.deemphasize)

        # Interval data, column1
        self.task_count_l.configure(foreground=self.highlight)
        self.tt_mean_l.configure(foreground=self.highlight)
        self.tt_sd_l.configure(foreground=self.emphasize)
        self.tt_range_l.configure(foreground=self.emphasize)
        self.tt_total_l.configure(foreground=self.emphasize)

        # Summary data, column2, deemphasize font color
        self.task_count_sumry_l.configure(foreground=self.deemphasize)
        self.ttmean_sumry_l.configure(foreground=self.deemphasize)
        self.ttsd_sumry_l.configure(foreground=self.deemphasize)
        self.ttrange_sumry_l.configure(foreground=self.deemphasize)
        self.ttsum_sumry_l.configure(foreground=self.deemphasize)

    def emphasize_sumry_data(self) -> None:
        """
        Switches font emphasis from Interval data to Summary data.
        Called from 'Summary data' button.
        """
        self.interval_t_l.config(foreground=self.deemphasize)
        self.summary_t_l.config(foreground=self.emphasize)

        # Summary data, column2, emphasize font color
        self.task_count_sumry_l.configure(foreground=self.highlight)
        self.ttmean_sumry_l.configure(foreground=self.highlight)
        self.ttsd_sumry_l.configure(foreground=self.emphasize)
        self.ttrange_sumry_l.configure(text=self.share.data['tt_range'].get(),
                                       foreground=self.emphasize)
        self.ttsum_sumry_l.configure(foreground=self.emphasize)

        # Interval data, column1, deemphasize font color
        self.task_count_l.configure(foreground=self.deemphasize)
        self.task_count_l.configure(foreground=self.deemphasize)
        self.tt_mean_l.configure(foreground=self.deemphasize)
        self.tt_sd_l.configure(foreground=self.deemphasize)
        self.tt_range_l.configure(foreground=self.deemphasize)
        self.tt_total_l.configure(foreground=self.deemphasize)

    @staticmethod
    def show_log() -> None:
        """
        Create a separate window to view the log file, read-only,
        scrolled text. Called from File menu.
        """
        os_width = 0
        if MY_OS in 'lin, win':
            os_width = 79
        elif MY_OS == 'dar':
            os_width = 72

        try:
            with open(LOGFILE, 'r') as file:
                logwin = tk.Toplevel()
                # logwin.title('count-tasks_log.txt')
                logwin.title(f'{LOGFILE}')
                if MY_OS in 'lin, dar':
                    logwin.minsize(725, 200)
                elif MY_OS == 'win':
                    logwin.minsize(800, 200)
                logwin.focus_set()
                logtext = ScrolledText(logwin, width=os_width, height=30,
                                       font='TkFixedFont',
                                       bg='grey85', relief='raised', padx=5)
                logtext.insert(tk.INSERT, file.read())
                logtext.see('end')
                logtext.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

                def reload():
                    with open(LOGFILE, 'r') as new_text:
                        logtext.delete(tk.INSERT, tk.END)
                        logtext.insert(tk.INSERT, new_text.read())
                        logtext.see('end')
                        logtext.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

                ttk.Button(logwin, text='Reload', command=reload).pack()
        except FileNotFoundError:
            warn_main = f'Log {LOGFILE} cannot be found.'
            warn_detail = ('Log file should be in folder:\n'
                           f'{CWD}\n'
                           'Has it been moved or renamed?')
            # print('\n', warn_main, warn_detail)
            messagebox.showwarning(title='FILE NOT FOUND',
                                   message=warn_main, detail=warn_detail)

    @staticmethod
    def backup_log() -> None:
        """
        Copy the log file to the home folder. Overwrites current file.
        Called from File menu.

        :return: A new or overwritten backup file.
        """

        destination = Path.home() / BKUPFILE
        if Path.is_file(LOGFILE) is True:
            try:
                shutil.copyfile(LOGFILE, destination)
                success_msg = 'Log file has been copied to: '
                success_detail = str(destination)
                # print(success_msg)
                messagebox.showinfo(title='Archive completed',
                                    message=success_msg, detail=success_detail)
            except PermissionError:
                print("Log file backup: Permission denied.")
            except IsADirectoryError:
                print("Log file backup: Destination is a directory.")
            except shutil.SameFileError:
                print("Log file backup: Source and destination are the same file.")
        else:
            warn_main = f'Log {LOGFILE} cannot be archived'
            warn_detail = ('Log file should be in folder:\n'
                           f'{CWD}\n'
                           'Has it been moved or renamed?')
            messagebox.showwarning(title='FILE NOT FOUND',
                                   message=warn_main, detail=warn_detail)
            # print('\n', warn_main, warn_detail)


class CountController(tk.Tk):
    """
    The Controller through which other MVC Count Classes can interact.
    """

    def __init__(self):
        super().__init__()

        # Need window sizes to make room for multi-line notices,
        # but not get minimized enough to exclude notices row.
        # Need OS-specific master window sizes b/c of different default font widths.
        if MY_OS == 'lin':
            self.minsize(550, 320)
            self.maxsize(780, 400)
            # Need geometry so that master window will be under settings()
            # Toplevel window at startup for Windows and Linux, not MacOS.
            # These x, y coordinates match default system placement on Ubuntu desktop.
            self.geometry('+96+134')
        elif MY_OS == 'win':
            self.minsize(500, 350)
            self.maxsize(702, 400)
            self.geometry('+96+134')
        elif MY_OS == 'dar':
            self.minsize(550, 350)
            self.maxsize(745, 400)
            # self.geometry('+96+134')

        # pylint: disable=assignment-from-no-return
        container = tk.Frame(self).grid()
        CountViewer(master=container, share=self)

    def defaultsettings(self) -> None:
        """
        Starting settings of: report interval, summary interval,
        counting limit, and log file option.
        """
        CountModeler(share=self).default_settings()

    def getminutes(self, timestring: str) -> int:
        """
        Converts a time string into minutes.

        :param timestring: value+unit, e.g. 60m, 12h, or 2d.
        :return: converted minutes as integer
        """
        return CountModeler(share=self).get_minutes(timestring)

    def setstartdata(self, *args) -> None:
        """
        Is called from Viewer.startup().
        """
        CountModeler(share=self).set_start_data()

    def formatsec(self, seconds: int, time_format: str) -> None:
        """
        Coverts seconds to formatted time string.

        :param seconds: Time in seconds, any integer except 0.
        :param time_format: Either 'std' or 'short'

        :return: 'std' time as 00:00:00; 'short' as s, m, h, or d.
        """
        CountModeler(share=self).format_sec(seconds, time_format)

    # pylint: disable=unused-argument
    def setintervaldata(self, *args) -> None:
        """
        Is called from Viewer.display_data(),
        in which get_ttime_stats() returns dictionary of time statistics.
        """
        CountModeler(share=self).set_interval_data()

    # pylint: disable=unused-argument
    def quitgui(self, *args) -> None:
        """Close down program. Called from button, menu, and keybinding.
        """
        CountModeler(share=self).quit_gui()

    # pylint: disable=unused-argument
    def complimentme(self, *args) -> None:
        """Is called from Help menu. A silly diversion.

        :param args: Needed for keybinding
        """
        CountFyi(share=self).compliment_me()

    def about(self):
        """Is called from Viewer Help menu.
        """
        CountFyi(share=self).about()


class CountFyi:
    """
    Modules to provide user information and help.
    """

    def __init__(self, share):
        self.share = share

    def compliment_me(self) -> None:
        """A silly diversion; called from Help menu and keybinding.

        :return: Transient label to make one smile.
        """
        compliments = [
            "Hey there good lookin'!", 'I wish we had met sooner.',
            'You are the smartest person I know.', 'I like your hair.',
            'You have such a nice smile.', 'Smart move!',
            'Blue is your color.', 'Good choice!',
            "That's very kind of you.", "Stop! You're making me blush.",
            'I just love what you did.', 'How witty you are!', 'Awesome!',
            'Your tastes are impeccable.', "You're incredible!",
            'You are so talented!', "I wish I'd thought of that.",
            'This is fun!', 'Get back to work.', 'Nice!', 'You saved me.',
            'You are an inspiration to us all.', "That's so funny!",
            'Show me how you do that.', "I've always looked up to you.",
            'You sound great!', 'You smell nice.', 'Great job!',
            'You are a role model.', 'I wish more people were like you.',
            'We appreciate what you did.', 'I hear people look up to you.',
            'You are a really good dancer.', 'What makes you so successful?',
            'When you speak, people listen.', 'You are a superb person.',
            'You rock!', 'You nailed it!', 'That was really well done.',
            'You are amazing!', 'We need more folks like you around here.',
            'Excuse me, are you a model?', 'What a lovely laugh you have.',
            "I'm jealous of your ability.", "You're the stuff of legends.",
            'This would not be possible without you.', 'Way to go! Yay!',
            'Did you make that? I love it!', 'You are the best!',
            'I like what you did.', 'Whoa. Have you been working out?',
            "We can't thank you enough.", 'No, really, you have done enough.',
            "That's a good look for you.", 'I could not have done it better.',
            "I can't think of anything to say. Sorry.", 'Congratulations!',
            "Well, THAT's impressive.", 'I hear that you are the one.',
            'You excel at everything.', 'Your voice is very soothing.',
            'Is it true what people say?', 'The word is, you got it!',
            'The Nobel Committee has been trying to reach you.',
            'The Academy is asking for your CV.', 'You look great!',
            'The President seeks your council.', 'Thank you so much!',
            'The Prime Minister seeks your council.', 'Crunchers rule!',
            'Crunchers are the best sort of people.'
        ]
        praise = random.choice(compliments)
        self.share.compliment_txt.config(text=praise)
        self.share.notice_l.grid_remove()
        # Need to re-grid initial master_widgets gridding b/c its grid may
        #   have been removed by a notice_txt_l call.
        self.share.compliment_txt.grid(row=13, column=1, columnspan=2,
                                       pady=5, sticky=tk.W)

        def refresh():
            self.share.compliment_txt.config(text="")
            app.update_idletasks()

        self.share.compliment_txt.after(3000, refresh)

    @staticmethod
    def about() -> None:
        """
        Basic information for gcount-tasks;
        Toplevel window called from Help menu.
        """
        aboutwin = tk.Toplevel()
        aboutwin.resizable(False, False)
        aboutwin.title('About count-tasks')
        colour = ['SkyBlue4', 'DarkSeaGreen4', 'DarkGoldenrod4', 'DarkOrange4',
                  'grey40', 'blue4', 'navy', 'DeepSkyBlue4', 'dark slate grey',
                  'dark olive green', 'grey2', 'grey25', 'DodgerBlue4',
                  'DarkOrchid4']
        bkg = random.choice(colour)
        num_doc_lines = __doc__.count('\n') + 2
        os_width = 0
        if MY_OS in 'lin, win':
            os_width = 62
        elif MY_OS == 'dar':
            os_width = '54'
        abouttxt = tk.Text(aboutwin, font='TkTextFont',
                           width=os_width, height=num_doc_lines + 7,
                           bg=bkg, fg='grey98', relief='groove',
                           borderwidth=5, padx=25)
        abouttxt.insert(1.0, f'{__doc__}\n'
                             f'Author:    {__author__}\n'
                             f'Credits:   {__credits__}\n'
                             f'License:   {__license__}\n'
                             f'URL:       {__project_url__}\n'
                             f'Version:   {__version__}\n'
                             f'Status:    {__status__}\n')
        abouttxt.pack()


if __name__ == "__main__":
    try:
        app = CountController()
        app.title("Count BOINC tasks")
        app.mainloop()
    except KeyboardInterrupt:
        exit_msg = (f'\n\n  *** Interrupted by user ***\n'
                    f'  Quitting now...{datetime.now()}\n\n')
        # sys.stdout.write(exit_msg)
        print(exit_msg)
        logging.info(msg=exit_msg)
