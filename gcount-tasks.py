#!/usr/bin/env python3

"""
GcountTasks (gcount-tasks) provides task counts and time statistics at
timed intervals for tasks recently reported to BOINC servers. It can be
run on Windows, Linux, or macOS. It is the tkinter GUI version of
count-tasks. Its MVC architecture is modified from examples provided
at https://stackoverflow.com/questions/32864610/ and links therein.

Requires Python 3.6 or later and tkinter (tk/tcl) 8.6 or later.
"""
# Copyright (C) 2021-2024 C.S. Echt, under GNU General Public License

# Standard library imports:
import logging
import sys
import threading
from datetime import datetime
from pathlib import Path
from random import choice
from socket import gethostname
from time import sleep, time
from typing import Union

# Third party imports (tk may not be included in some Python installations):
try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except (ImportError, ModuleNotFoundError) as error:
    sys.exit('This program requires tkinter, which is included with \n'
             'Python 3.7+ distributions.\n'
             'Install the most recent version or re-install Python and include Tk/Tcl.\n'
             '\nOn Linux, you may also need: $ sudo apt-get install python3-tk\n'
             f'See also: https://tkdocs.com/tutorial/install.html \n'
             f'Error msg: {error}')

# Local program imports:
import count_modules as cmod
from count_modules import (binds,
                           boinc_commands as bcmd,
                           config_constants as const,
                           files,
                           instances,
                           times,
                           utils,
                           )
from count_modules.logs import Logs

PROGRAM_NAME = instances.program_name()


class Notices:
    """
    Attributes and methods used by CountModeler.update_notice_text() to
    provide notices to the user about the status of BOINC tasks and projects.
    """

    def __init__(self, share):
        self.share = share

        # Set instance attributes for use in update_notice_text() dispatch tables and in
        #  the following Class methods. These attributes are set in
        #  CountModeler.update_task_status().
        self.num_suspended_by_user = self.share.notice['num_suspended_by_user'].get()
        self.num_uploading = self.share.notice['num_uploading'].get()
        self.num_uploaded = self.share.notice['num_uploaded'].get()
        self.num_aborted = self.share.notice['num_aborted'].get()
        self.num_err = self.share.notice['num_err'].get()
        self.num_tasks_all = self.share.data['num_tasks_all'].get()
        self.num_taskless_intervals = self.share.notice['num_taskless_intervals'].get()
        self.num_running = self.share.notice['num_running'].get()

    # These methods are called by the tasks_running dispatch table in
    #  CountModeler.update_notice_text().
    def suspended_by_user(self, called_by=None) -> str:
        """
        Is used to provide context-specific text for log_it() and
        update_notice_text() methods.

        Args: called_by: Either 'log' or None. If 'log', then the
            method is called from log_it() and the return value is
            formatted for logging. If None, then the return value is
            formatted for GUI display via update_notice_text() dispatch table.
        Returns: A string with the appropriate notice text.
        """
        if called_by == 'log':
            return f'{self.num_suspended_by_user} tasks were suspended by user.\n'

        # The other called_by value is from the update_notice_text() dispatch table.
        return (f'{self.num_suspended_by_user} tasks are suspended by user.\n'
                f'BOINC will not upload while tasks are suspended.')

    @staticmethod
    def running_out_of_tasks():
        return 'BOINC client is about to run out of tasks.\nCheck BOINC Manager.'

    def no_tasks_reported(self):
        return ('NO TASKS reported for the prior'
                f' {self.num_taskless_intervals} counting interval(s).')

    def computation_error(self):
        """Is used in both tasks_running and no_tasks_running dispatch tables."""
        return (f'{self.num_err} tasks have a Computation error.\n'
                f'Check BOINC Manager. Check the E@H msg boards.')

    def all_is_well(self):
        self.share.notice_l.config(fg=self.share.row_fg)
        return f'All is well (updates every {const.NOTICE_INTERVAL} seconds)'

    # These methods are called by the no_tasks_running dispatch table in
    #  CountModeler.update_notice_text().
    def no_tasks(self):
        if self.share.notice['no_new_tasks'].get():
            return ('BOINC client has no tasks to run!\n'
                    'Project is set to receive no new tasks.')
        return 'BOINC client has no tasks to run!\nCheck BOINC Manager.'

    def user_suspended_tasks(self):
        return (
            f'NO TASKS running; {self.num_suspended_by_user} tasks suspended by user.\n'
            'You may want to resume them.'
        )

    @staticmethod
    def user_suspended_activity():
        return ('NO TASKS running.\n'
                'Activity suspended by user request or Computing preferences.')

    @staticmethod
    def user_suspended_project():
        return ('NO TASKS running.\n'
                'Project suspended by user request or Computing preferences.')

    @staticmethod
    def boinc_suspended_tasks():
        return ('NO TASKS running.\n'
                'A BOINC Manager "When to suspend" condition was met.\n'
                'Edit BOINC Manager Computing preferences if this is a problem.')

    def all_stalled(self) -> Union[bool, str]:
        """
        Is also called as a condition in the no_tasks_running dispatch
        table because its condition is too lengthy to use in the table.
        Therefore, to properly evaluate a False condition, must specify
        the return value as a Boolean instead of leaving it as None.
        """
        if self.num_uploading + self.num_uploaded + self.num_aborted == self.num_tasks_all:
            return (
                'All tasks are stalled Uploading, Ready to report, or Aborted.\n'
                'Check your Project message boards for server issues.')
        return False

    @staticmethod
    def unknown():
        return '15 sec status update: NO TASKS RUNNING, reason unknown.'


# ############################ MVC Classes #############################
# MVC Modeler: The engine that gets BOINC data and runs count intervals.
class CountModeler:
    """
    Counting, statistical analysis, and formatting of BOINC task data.
    Communication with the Viewer Class for data display occurs via
    the 'share' parameter.

    Methods:
    default_settings
    start_data
    update_task_status
    interval_data
    manage_notices
    get_dispatch_table
    update_notice_text
    post_final_notice
    log_it
    """

    def __init__(self, share):
        self.share = share
        self.thread_lock = threading.Lock()

    def default_settings(self) -> None:
        """
        Set or reset default run parameters in the setting dictionary.
        """
        self.share.setting['interval_t'].set('1h')
        self.share.setting['interval_m'].set(60)
        self.share.intvl_choice['values'] = ('1h', '30m', '20m', '15m', '10m')
        self.share.intvl_choice.select_clear()
        self.share.setting['summary_t'].set('1d')
        self.share.setting['sumry_t_value'].set(1)
        self.share.setting['sumry_t_unit'].set('day')
        self.share.sumry_unit_choice['values'] = ('day', 'hr', 'min')
        self.share.sumry_unit_choice.select_clear()
        self.share.setting['cycles_max'].set(1008)
        self.share.setting['do_log'].set(True)
        self.share.setting['sound_beep'].set(False)

    def start_data(self, called_from: str) -> set:
        """
        Gather initial task data and times; set data dictionary
        control variables. Log data to file if so optioned.
        Called from startdata(), interval_data().

        Args: called_from: Either 'start' to write starting data to log
            or 'interval_data' to use the return set of tasks.

        Returns: The set of starting task times.
        """
        # As with task names, task times as sec.microsec are unique.
        #   In the future, may want to inspect task names with
        #     tnames = bcmd.get_reported('tasks').
        ttimes_start = bcmd.get_reported('elapsed time')
        self.share.data['task_count'].set(len(ttimes_start))
        self.share.data['num_tasks_all'].set(len(bcmd.get_tasks('name')))

        startdict = times.boinc_ttimes_stats(ttimes_start)
        self.share.data['taskt_avg'].set(startdict['taskt_avg'])
        self.share.data['taskt_sd'].set(startdict['taskt_sd'])
        self.share.data['taskt_range'].set(
            f"{startdict['taskt_min']} -- {startdict['taskt_max']}")
        self.share.data['taskt_total'].set(startdict['taskt_total'])

        self.share.data['time_prev_cnt'].set('Last hourly BOINC report.')

        if self.share.setting['do_log'].get() and called_from == 'start':
            self.share.logit('start')

        # Begin keeping track of the set of used/old tasks to exclude
        #   from new tasks; pass to in interval_data() to track tasks
        #   across intervals.
        return set(ttimes_start)

    def update_task_status(self) -> None:
        """
        Query boinc-client for status of tasks queued, running, and
        suspended; set corresponding dictionary tk control variables.
        Called from update_notice_text().
        """

        self.share.status_time = datetime.now().strftime(const.LONG_FMT)
        tasks_all = bcmd.get_tasks('all')
        state_all = bcmd.get_state()

        # Need the literal task data tag as found in boinccmd stdout;
        #   the format is same as tag_str in bcmd.get_tasks().
        tag = {'name': '   name: ',
               'active': '   active_task_state: ',
               'state': '   state: ',
               'sched state': '   scheduler state: '}

        num_tasks_all = len([elem for elem in tasks_all if tag['name'] in elem])
        active_task_states = [elem.replace(tag['active'], '') for elem in tasks_all
                              if tag['active'] in elem]
        task_states = [elem.replace(tag['state'], '') for elem in tasks_all
                       if tag['state'] in elem]
        scheduler_states = [elem.replace(tag['sched state'], '') for elem in tasks_all
                            if tag['sched state'] in elem]

        num_running = len(
            [task for task in active_task_states if 'EXECUTING' in task])

        # Condition when activity is suspended BOINC Manager based on
        #  Computing preferences for CPU in use.
        num_suspended_cpu_busy = len(
            [task for task in active_task_states if 'SUSPENDED' in task])
        num_suspended_by_user = len(
            [task for task in tasks_all if 'suspended via GUI: yes' in task])

        # Use as a Boolean variable expressed as 0 or 1.
        project_suspended_by_user = len(
            [item for item in state_all if 'suspended via GUI: yes' in item])

        # Condition when activity is suspended either by user or by BOINC Manager
        #  based on Computing preferences for "Computer in use" or the time of day.
        num_activity_suspended = len(
            [task for task in active_task_states if 'UNINITIALIZED' in task and
             'scheduled' in scheduler_states])
        num_uploading = len(
            [task for task in task_states if 'uploading' in task])
        num_uploaded = len(
            [task for task in task_states if 'uploaded' in task])
        num_err = len(
            [task for task in task_states if 'compute error' in task])
        num_aborted = len(
            [task for task in active_task_states if 'ABORT_PENDING' in task])

        self.share.data['num_tasks_all'].set(num_tasks_all)
        self.share.notice['num_running'].set(num_running)
        self.share.notice['num_suspended_cpu_busy'].set(num_suspended_cpu_busy)
        self.share.notice['num_suspended_by_user'].set(num_suspended_by_user)
        self.share.notice['project_suspended_by_user'].set(project_suspended_by_user)
        self.share.notice['num_activity_suspended'].set(num_activity_suspended)
        self.share.notice['no_new_tasks'].set(bcmd.no_new_tasks())
        self.share.notice['num_uploading'].set(num_uploading)
        self.share.notice['num_uploaded'].set(num_uploaded)
        self.share.notice['num_aborted'].set(num_aborted)
        self.share.notice['num_err'].set(num_err)

    def interval_data(self) -> None:
        """
        Run timer and countdown clock to update and analyze regular and
        summary data for task status and times. Set control variables
        for data and notice dictionaries.
        Is threaded as interval_thread; started in Viewer.start_threads().
        Calls to: get_minutes(), log_it().
        """

        # ttimes_used is the set of starting task times.
        ttimes_used = self.start_data(called_from='interval_data')
        ttimes_new = set()
        ttimes_smry = set()
        cycles_max = self.share.setting['cycles_max'].get()
        interval_m = self.share.setting['interval_m'].get()
        reference_time = time()
        num_taskless_intervals = 0
        sumry_intvl_counts = []
        sumry_intvl_ttavgs = []

        for cycle in range(cycles_max):
            if cycle == 1:
                # Need to change button name and function from Start to Interval
                #   after initial cycle[0] completes and intvl data displays.
                #  It might be better if statement were in Viewer, but simpler
                #  to put it here with easy reference to cycle.
                self.share.intvl_b.grid(row=0, column=1,
                                        padx=(16, 0), pady=(8, 4))
                self.share.starting_b.grid_forget()
            # Need to sleep between counts while displaying a countdown timer.
            # Need to limit total time of interval to target_elapsed_time,
            #   in Epoch seconds, b/c each interval sleep cycle will run longer
            #   than the intended interval. Realized interval time should thus
            #   not drift by more than 1 second during count_max cycles.
            #   Without this time limit, each 1h interval would gain ~4s.
            interval_sec = interval_m * 60
            target_elapsed_time = reference_time + (interval_sec * (cycle + 1))
            for _sec in range(interval_sec):
                if cycle == cycles_max:
                    break
                if time() > target_elapsed_time:
                    self.share.data['time_next_cnt'].set('00:00')
                    break
                interval_sec -= 1
                # Need to show the time remaining in clock time format.
                self.share.data['time_next_cnt'].set(
                    times.sec_to_format(interval_sec, 'clock'))
                sleep(1.0)

            # NOTE: Starting tasks are not included in interval and summary
            #   counts, but starting task times are used here to determine
            #   "new" tasks.
            # Need to add all prior tasks to the "used" set.
            #  "new" task times are carried over from the prior interval cycle.
            #  For cycle[0], ttimes_used is starting tasks from start_data()
            #    and ttimes_new is empty.
            with self.thread_lock:
                ttimes_used.update(ttimes_new)
                ttimes_reported = set(bcmd.get_reported('elapsed time'))

                # Need to reset prior ttimes_new, then repopulate it with only
                #   newly reported tasks.
                ttimes_new.clear()
                ttimes_new = ttimes_reported - ttimes_used

                task_count_new = len(ttimes_new)
                self.share.data['task_count'].set(task_count_new)

                cycles_remain = int(self.share.data['cycles_remain'].get()) - 1
                self.share.data['cycles_remain'].set(cycles_remain)

                # Display weekday with time of previous interval to aid the user.
                self.share.data['time_prev_cnt'].set(
                    datetime.now().strftime(const.DAY_FMT))
                # Capture full ending time here, instead of in log_it(),
                #   so that the logged time matches displayed time.
                self.share.data['time_intvl_count'].set(
                    datetime.now().strftime(const.LONG_FMT))

                # Track when no new tasks were reported in past interval;
                #   num_taskless_intervals used in get_dispatch_table().
                # Need to update num_running value from task_states().
                self.update_task_status()
                num_running = self.share.notice['num_running'].get()
                if task_count_new == 0:
                    num_taskless_intervals += 1
                elif task_count_new > 0 and num_running > 0:
                    num_taskless_intervals = 0
                self.share.notice['num_taskless_intervals'].set(num_taskless_intervals)

                intervaldict = times.boinc_ttimes_stats(ttimes_new)
                self.share.data['taskt_avg'].set(intervaldict['taskt_avg'])
                self.share.data['taskt_sd'].set(intervaldict['taskt_sd'])
                self.share.data['taskt_range'].set(
                    f"{intervaldict['taskt_min']} -- {intervaldict['taskt_max']}")
                self.share.data['taskt_total'].set(intervaldict['taskt_total'])

                # SUMMARY DATA #########################################
                # NOTE: Starting data are not included in summary tabulations.
                # Need to gather interval times and counts for ea. interval in
                #   a summary segment to calc weighted mean times. This sumry
                #   list has a different function than the ttimes_smry set.
                sumry_intvl_counts.append(task_count_new)
                sumry_intvl_ttavgs.append(self.share.data['taskt_avg'].get())
                ttimes_smry.update(ttimes_new)

                summary_m = times.string_to_min(self.share.setting['summary_t'].get())
                # When summary interval is >= 1 week, need to provide date of
                #   prior summary rather than weekday, as above (%A %H:%M).
                # Take care that the summary time_now exactly matches the
                #   time of the last interval in the summary period.
                if summary_m >= 10080:
                    self.share.data['time_prev_cnt'].set(
                        datetime.now().strftime(const.SHORTER_FMT))
                if (cycle + 1) % (summary_m // interval_m) == 0:
                    self.update_summary_data(
                        time_prev=self.share.data['time_prev_cnt'].get(),
                        tasks=ttimes_smry,
                        averages=sumry_intvl_ttavgs,
                        counts=sumry_intvl_counts
                    )

                    # Need to reset data for the next summary interval.
                    ttimes_smry.clear()
                    sumry_intvl_ttavgs.clear()
                    sumry_intvl_counts.clear()

            # Call to log_it() needs to be outside the thread lock.
            app.update_idletasks()
            if self.share.setting['do_log'].get():
                self.share.logit('interval')

    def update_summary_data(self,
                            time_prev: str,
                            tasks: set,
                            averages: list,
                            counts: list) -> None:
        """
        Set summary data for the most recent interval.
        Called from CountModeler.interval_data().
        Calls times.logtimes_stat() and times.boinc_ttimes_stats().

        Args:
            time_prev: The time of the previous summary interval.
            tasks: A set of task times for the most recent interval.
            averages: A list of average task times for each interval.
            counts: A list of new task counts since previous interval.
        Returns:
             None
        """
        # Flag used in log_it() to log summary data.
        self.share.data['log_summary'].set(True)

        # Need to deactivate tooltip and activate the Summary
        #   data button now; only need this for the first Summary
        #   but, oh well, here we go again...
        utils.Tooltip(widget=self.share.sumry_b, tt_text='', state='disabled')
        self.share.sumry_b.config(state=tk.NORMAL)

        # Set time and stats of summary count.
        self.share.data['time_prev_sumry'].set(time_prev)
        self.share.data['task_count_sumry'].set(len(tasks))
        summarydict = times.boinc_ttimes_stats(tasks)
        self.share.data['taskt_sd_sumry'].set(summarydict['taskt_sd'])
        self.share.data['taskt_range_sumry'].set(
            f"{summarydict['taskt_min']} -- {summarydict['taskt_max']}")
        self.share.data['taskt_total_sumry'].set(summarydict['taskt_total'])

        # Need the weighted mean summary task time, not the average
        #   (arithmetic mean) value.
        taskt_weighted_mean: str = times.logtimes_stat(
            distribution=averages,
            stat='weighted_mean',
            weights=counts)
        self.share.data['taskt_mean_sumry'].set(taskt_weighted_mean)

    def manage_notices(self):
        """
        Manages BOINC task state information and notifications by
        running on short time intervals. A const.NOTICE_INTERVAL of 15 sec
        works well.
        Is threaded as notice_thread in CountViewer.start_threads() with
        target of Countcontroller.taskstatenotices().
        Calls to: Notice(), bcmd.check_boinc_tk(), utils.beep(),
            update_notice_text(), and post_final_notice().
        """

        while self.share.data['cycles_remain'].get() > 0:
            sleep(const.NOTICE_INTERVAL)
            bcmd.check_boinc_tk(app)

            with self.thread_lock:
                self.update_notice_text()  # also calls update_task_status().
                if (self.share.notice['num_running'].get() == 0
                        and self.share.setting['sound_beep'].get()):
                    utils.beep(repeats=2)

            if self.share.data['cycles_remain'].get() == 0:
                self.post_final_notice()

            app.update_idletasks()

            # Call to log_it() needs to be outside the thread lock.
            if self.share.setting['do_log'].get():
                self.share.logit('notice')

    def get_dispatch_table(self, Note) -> dict:
        """ Returns a dispatch table for update_notice_text() based on whether
         tasks running or not. Called from update_notice_text(). Calls Notices()

        Args:
            Note: An attribute of the Notices class that is used to
                obtain current task status values and text relevant to
                task status.
        Returns:
            A dispatch table to post relevant GUI notices based on
            current task status conditions.
        """
        num_suspended_cpu_busy = self.share.notice['num_suspended_cpu_busy'].get()
        num_activity_suspended = self.share.notice['num_activity_suspended'].get()
        project_suspended_by_user = self.share.notice['project_suspended_by_user'].get()

        # Status values and notice text are from Notices() instances.
        # Dispatch table items are in descending order of status
        #  notification priority.
        tasks_running = {
            Note.num_suspended_by_user > 0: Note.suspended_by_user,
            Note.num_running >= (Note.num_tasks_all - 1): Note.running_out_of_tasks,
            Note.num_taskless_intervals > 0: Note.no_tasks_reported,
            Note.num_err > 0: Note.computation_error,
        }

        no_tasks_running = {
            Note.num_tasks_all == 0: Note.no_tasks,
            Note.num_suspended_by_user > 0: Note.user_suspended_tasks,
            num_suspended_cpu_busy > 0: Note.boinc_suspended_tasks,
            num_activity_suspended > 0: Note.user_suspended_activity,
            project_suspended_by_user: Note.user_suspended_project,
            Note.all_stalled(): Note.all_stalled,
            Note.num_err > 0: Note.computation_error,
        }

        return tasks_running if Note.num_running > 0 else no_tasks_running

    def update_notice_text(self):
        """
        Grabs the most recent task status data.
        Called from manage_notices().
        Calls Notices() and get_dispatch_table().
        """

        self.update_task_status()
        Note = Notices(self.share)
        dispatch_table = self.get_dispatch_table(Note)
        for condition, func in dispatch_table.items():
            if condition is True:
                self.share.notice_l.config(fg=self.share.highlight)
                self.share.notice['notice_txt'].set(func())
                return

        # If no known problem is found when no tasks are running,
        #  then post "reason unknown" notice. Otherwise, post "all is well".
        status = 'unknown' if Note.num_running == 0 else 'all is well'
        self.share.notice_l.config(
            fg=self.share.highlight if status == 'unknown' else self.share.row_fg)
        self.share.notice['notice_txt'].set(
            Note.unknown() if status == 'unknown' else Note.all_is_well())

    def post_final_notice(self):
        """Called from manage_notices()."""
        cycles_max = self.share.setting['cycles_max'].get()
        self.share.notice['notice_txt'].set(
            f'{self.share.notice["notice_txt"].get()}\n'
            f'*** All {cycles_max} count intervals have been run. ***\n')
        print(f'\n*** {cycles_max} of {cycles_max} counting cycles have ended. ***\n'
              'You can quit the program from the GUI, then restart from the command line.\n')

    def log_it(self, called_from: str) -> None:
        """
        Write interval and summary metrics for recently reported
        BOINC tasks. Provide information on aberrant task status.
        Called from start_data(), interval_data(), update_notice_text(), and
        CountController.logit().
        Is threaded as log_thread in Viewer.start_threads().

        :param called_from: Either 'start', 'interval' or 'notice',
                            depending on type of data to be logged.
        """

        # Var used for log text formatting:
        indent = ' ' * 22
        bigindent = ' ' * 33
        cycles_max = self.share.setting['cycles_max'].get()

        def log_start():
            task_count = self.share.data['task_count'].get()
            taskt_avg = self.share.data['taskt_avg'].get()
            taskt_sd = self.share.data['taskt_sd'].get()
            taskt_range = self.share.data['taskt_range'].get()
            taskt_total = self.share.data['taskt_total'].get()
            num_tasks_all = self.share.data['num_tasks_all'].get()

            if cycles_max > 0:
                report = (
                    f'\n>>> START GUI TASK COUNTER v.{cmod.__version__}, SETTINGS: <<<\n'
                    f'{self.share.long_time_start};'
                    f' Number of tasks in the most recent BOINC report: {task_count}\n'
                    f'{indent}Task Time: avg {taskt_avg},\n'
                    f'{bigindent}range [{taskt_range}],\n'
                    f'{bigindent}stdev {taskt_sd}, total {taskt_total}\n'
                    f'{indent}Total tasks in queue: {num_tasks_all}\n'
                    f'{indent}Number of scheduled count intervals: {cycles_max}\n'
                    f'{indent}Counts every {self.share.setting["interval_t"].get()},'
                    f' summaries every {self.share.setting["summary_t"].get()}.\n'
                    f'{indent}BOINC status evaluations every {const.NOTICE_INTERVAL}s.\n'
                    'Timed intervals beginning now...\n')
            else:  # If cycles_max is 0, then the program is in test (status) mode.
                report = (
                    f'\n{self.share.long_time_start}; STATUS REPORT\n'
                    f'{indent}Number of tasks recently reported by BOINC: {task_count}\n'
                    f'{indent}Task Time: avg {taskt_avg},\n'
                    f'{bigindent}range [{taskt_range}],\n'
                    f'{bigindent}stdev {taskt_sd}, total {taskt_total}\n'
                    f'{indent}Total tasks in queue: {num_tasks_all}\n')

            logging.info(report)

        def log_interval():
            # Local vars that are either used more than once or to shorten f-strings.
            interval_t = self.share.setting['interval_t'].get()
            summary_t = self.share.setting['summary_t'].get()
            time_intvl_count = self.share.data['time_intvl_count'].get()
            taskt_sd = self.share.data['taskt_sd'].get()
            cycles_remain = self.share.data['cycles_remain'].get()

            logging.info(
                f'\n{time_intvl_count}; Tasks reported in the past {interval_t}:'
                f' {self.share.data["task_count"].get()}\n'
                f'{indent}Task Time: avg {self.share.data["taskt_avg"].get()},\n'
                f'{bigindent}range [{self.share.data["taskt_range"].get()}],\n'
                f'{bigindent}stdev {taskt_sd}, total {self.share.data["taskt_total"].get()}\n'
                f'{indent}Total tasks in queue: {self.share.data["num_tasks_all"].get()}\n'
                f'{indent}{cycles_remain} counts remain.')

            if self.share.data['log_summary'].get():
                logging.info(
                    f'\n{time_intvl_count}; >>> SUMMARY: Task count for the past'
                    f" {summary_t}: {self.share.data['task_count_sumry'].get()}\n"
                    f"{indent}Task Time: mean {self.share.data['taskt_mean_sumry'].get()},\n"
                    f"{bigindent}range [{self.share.data['taskt_range_sumry'].get()}],\n"
                    f"{bigindent}stdev {self.share.data['taskt_sd_sumry'].get()},"
                    f" total {self.share.data['taskt_total_sumry'].get()}")

                # Need to reset flag to toggle summary logging.
                self.share.data['log_summary'].set(False)

        def log_notice():
            """Need to grab the most recent task status data."""
            Note = Notices(self.share)

            if Note.num_running > 0:
                if Note.num_running >= self.share.data['num_tasks_all'].get() - 1:
                    logging.info(
                        f'\n{self.share.status_time}; {Note.running_out_of_tasks()}.')
                if Note.num_suspended_by_user > 0:
                    logging.info(
                        f'\n{self.share.status_time};'
                        f' {Note.suspended_by_user(called_by="log")}')
                if self.share.data['cycles_remain'].get() == 0:
                    logging.info(
                        f'\n*** All {cycles_max} count intervals have been run. ***\n'
                        ' Counting has ended.\n')

            else:  # no tasks are running
                # Log detailed status for all true conditions.
                # With Note.unknown() as last value in the not_tasks_running dispatch
                #  dict, log "reason unknown" only when a known problem is not found.
                dispatch_table = self.get_dispatch_table(Note)
                known_problem = False
                for condition, func in dispatch_table.items():
                    if condition is True:
                        logging.info(
                            f'\n{self.share.status_time}; {func()}')
                        known_problem = True
                if known_problem is False:
                    logging.info(
                        f'\n{self.share.status_time}; {Note.unknown()}')

        logging_functions = {
            'start': log_start,
            'interval': log_interval,
            'notice': log_notice,
        }

        with self.thread_lock:
            self.update_task_status()
            # Need this condition to avoid key error from the threading arg
            #  of None used for CountController.logit() in start_threads().
            try:
                if called_from:
                    logging_functions[called_from]()
            except KeyError as err:
                print('The called_from param in logit() is expected to be'
                      '"start", "notice", "interval" or None.\n', err)


# ###### MVC Viewer: the tkinter GUI engine; runs in main thread. ######
class CountViewer(tk.Frame):
    """
    The MVC Viewer represents the master Frame for the main window.
    All main window GUI and data widgets are defined here. Communication
    with the Modeler Class for data manipulation occurs via the 'share'
    parameter.
    """

    __slots__ = (
        'beep_choice',
        'countnow_button',
        'cycles_max_entry',
        'cycles_max_l',
        'cycles_remain_l',
        'data_bg',
        'dataframe',
        'deemphasize',
        'emphasize',
        'info_button_img',
        'interval_t_l',
        'log_choice',
        'master_bg',
        'menubar',
        'num_tasks_all_l',
        'settings_win',
        'share',
        'summary_t_l',
        'sumry_value_entry',
        'task_count_l',
        'task_count_sumry_l',
        'time_next_cnt_l',
        'time_prev_cnt_l',
        'time_prev_sumry_l',
        'time_start_l',
        'taskt_avg_l',
        'taskt_range_l',
        'taskt_sd_l',
        'taskt_total_l',
        'taskt_mean_sumry_l',
        'taskt_range_sumry_l',
        'taskt_sd_sumry_l',
        'taskt_total_sumry_l',
        'view_button_style'
    )

    def __init__(self, share):
        super().__init__()
        self.share = share
        self.dataframe = tk.Frame()
        self.menubar = tk.Menu()
        # self.master is an implicit internal attribute.

        # Set colors for row labels and data display.
        # These colors are compatible with red-green color-blindness.
        self.share.row_fg = 'LightYellow'  # Row header label fg.
        self.master_bg = 'SteelBlue4'  # app and header label bg.
        self.data_bg = 'grey40'  # Data labels and data frame bg.
        self.share.highlight = 'gold1'  # Notices, compliments, highlight fg.
        self.emphasize = 'grey90'  # Lighter data label fg, use for grey-out.
        self.deemphasize = 'grey60'  # Darker data label fg.

        # Need to grey-out menu bar headings and View log button when
        #   another application has focus.
        #   source: https://stackoverflow.com/questions/18089068/
        #   tk-tkinter-detect-application-lost-focus
        self.bind_all('<FocusIn>', self.app_got_focus)
        self.bind_all('<FocusOut>', self.app_lost_focus)

        # settings() window widgets:
        self.settings_win = tk.Toplevel()
        self.share.intvl_choice = ttk.Combobox(self.settings_win)
        self.sumry_value_entry = ttk.Entry(self.settings_win)
        self.share.sumry_unit_choice = ttk.Combobox(self.settings_win)
        self.cycles_max_entry = ttk.Entry(self.settings_win)
        self.countnow_button = ttk.Button(self.settings_win)
        self.log_choice = tk.Checkbutton(self.settings_win)
        self.beep_choice = tk.Checkbutton(self.settings_win)

        # Control variables for basic run parameters/settings passed
        #    between Viewer and Modeler.
        self.share.setting = {
            'interval_t': tk.StringVar(),
            'interval_m': tk.IntVar(),
            'sumry_t_value': tk.StringVar(),
            'sumry_t_unit': tk.StringVar(),
            'summary_t': tk.StringVar(),
            'cycles_max': tk.IntVar(),
            'do_log': tk.BooleanVar(),
            'sound_beep': tk.BooleanVar()
        }

        # Control variables for display in master; data passed between
        #    Viewer and Modeler.
        self.share.data = {
            # Start and Interval data
            'task_count': tk.IntVar(),
            'taskt_avg': tk.StringVar(),
            'taskt_sd': tk.StringVar(),
            'taskt_range': tk.StringVar(),
            'taskt_total': tk.StringVar(),
            'time_intvl_count': tk.StringVar(),
            # General data
            'time_prev_cnt': tk.StringVar(),
            'cycles_remain': tk.IntVar(),
            'time_next_cnt': tk.StringVar(),
            'num_tasks_all': tk.IntVar(),
            # Summary data
            'time_prev_sumry': tk.StringVar(),
            'task_count_sumry': tk.IntVar(),
            'taskt_mean_sumry': tk.StringVar(),
            'taskt_sd_sumry': tk.StringVar(),
            'taskt_range_sumry': tk.StringVar(),
            'taskt_total_sumry': tk.StringVar(),
            'log_summary': tk.BooleanVar(),
        }

        # Control variables for notices and logging passed between
        #   Viewer and Modeler and between Modeler threads.
        self.share.notice = {
            'notice_txt': tk.StringVar(),
            'num_running': tk.IntVar(),
            'num_taskless_intervals': tk.IntVar(),
            'project_suspended_by_user': tk.BooleanVar(),
            'no_new_tasks': tk.BooleanVar(),
            'num_suspended_by_user': tk.IntVar(),
            'num_suspended_cpu_busy': tk.IntVar(),
            'num_activity_suspended': tk.IntVar(),
            'num_uploading': tk.IntVar(),
            'num_uploaded': tk.IntVar(),
            'num_aborted': tk.IntVar(),
            'num_err': tk.IntVar(),
        }

        boinc_lbl_params = dict(
            master=self.dataframe,
            font=const.LABEL_FONT,
            width=3,
            bg=self.data_bg)

        master_row_params = dict(
            bg=self.master_bg,
            fg=self.share.row_fg)

        master_highlight_params = dict(
            bg=self.master_bg,
            fg=self.share.highlight)

        # Labels for settings values; gridded in master_layout(). They are
        #   fully configured here simply to reduce number of lines in code.
        # NOTE: self.time_start_l label is initially configured with text to
        #   show a startup message, then reconfigured in emphasize_start_data()
        #   to show the time_start.
        self.time_start_l = tk.Label(
            self.dataframe, bg=self.data_bg, fg=self.emphasize, )
        self.interval_t_l = tk.Label(
            self.dataframe, width=21, borderwidth=2,
            textvariable=self.share.setting['interval_t'],
            relief='groove', bg=self.data_bg)
        self.summary_t_l = tk.Label(
            self.dataframe, width=21, borderwidth=2,
            textvariable=self.share.setting['summary_t'],
            relief='groove', bg=self.data_bg)
        self.cycles_max_l = tk.Label(**master_row_params,
                                     textvariable=self.share.setting['cycles_max'])

        # Labels for BOINC data.
        self.task_count_l = tk.Label(**boinc_lbl_params,
                                     textvariable=self.share.data['task_count'])
        self.taskt_avg_l = tk.Label(**boinc_lbl_params,
                                    textvariable=self.share.data['taskt_avg'])
        self.taskt_sd_l = tk.Label(**boinc_lbl_params,
                                   textvariable=self.share.data['taskt_sd'])
        self.taskt_range_l = tk.Label(**boinc_lbl_params,
                                      textvariable=self.share.data['taskt_range'])
        self.taskt_total_l = tk.Label(**boinc_lbl_params,
                                      textvariable=self.share.data['taskt_total'])
        self.task_count_sumry_l = tk.Label(**boinc_lbl_params,
                                           textvariable=self.share.data['task_count_sumry'])
        self.taskt_mean_sumry_l = tk.Label(**boinc_lbl_params,
                                           textvariable=self.share.data['taskt_mean_sumry'])
        self.taskt_sd_sumry_l = tk.Label(**boinc_lbl_params,
                                         textvariable=self.share.data['taskt_sd_sumry'])
        self.taskt_range_sumry_l = tk.Label(**boinc_lbl_params,
                                            textvariable=self.share.data['taskt_range_sumry'])
        self.taskt_total_sumry_l = tk.Label(**boinc_lbl_params,
                                            textvariable=self.share.data['taskt_total_sumry'])

        # Master data labels (self.master is implicit as the parent).
        self.time_prev_cnt_l = tk.Label(**master_row_params,
                                        textvariable=self.share.data['time_prev_cnt'])
        self.time_prev_sumry_l = tk.Label(**master_row_params,
                                          textvariable=self.share.data['time_prev_sumry'])
        self.cycles_remain_l = tk.Label(**master_row_params,
                                        textvariable=self.share.data['cycles_remain'])
        self.num_tasks_all_l = tk.Label(**master_row_params,
                                        textvariable=self.share.data['num_tasks_all'])
        self.time_next_cnt_l = tk.Label(**master_highlight_params,
                                        textvariable=self.share.data['time_next_cnt'])

        # Text for compliment_l is configured in compliment_me()
        self.share.compliment_l = tk.Label(**master_highlight_params, )
        self.share.notice_l = tk.Label(**master_highlight_params,
                                       textvariable=self.share.notice['notice_txt'],
                                       relief='flat', border=0)

        # This style is used only to configure viewlog_b color in
        #   app_got_focus() and app_lost_focus().
        #   self.master is implicit as the parent.
        self.view_button_style = ttk.Style()

        # Need to define image as a class variable, not a local var in methods.
        self.info_button_img = tk.PhotoImage(
            file=files.valid_path_to('images/info_button20.png'))

        self.master_widgets()
        self.master_layout()
        self.share.defaultsettings()
        self.settings()
        self.settings_tooltips()

    def master_widgets(self) -> None:
        """
        Master app menus and buttons.
        """

        # Note that self.master is an internal attribute of the
        #   BaseWidget Class in tkinter's __init__.pyi. Here it refers to
        #   the CountController() Tk mainloop window. In CountViewer lambda
        #   functions, MAY use 'app' in place of self.master, but outside
        #   CountViewer, MUST use 'app' for any mainloop reference.

        self.master.config(menu=self.menubar)

        # Add pull-down menus
        file = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label='File', menu=file)
        file.add_command(
            label='Backup log file',
            command=lambda: files.save_as(Logs.LOGFILE))
        file.add_command(
            label='Backup analysis file',
            command=lambda: files.save_as(Logs.ANALYSISFILE))
        file.add_separator()
        file.add_command(label='Quit', command=lambda: utils.quit_gui(app),
                         accelerator='Ctrl+Q')
        # ^^ Note: use Ctrl+Q for macOS also to call utils.quit_gui;
        #    Cmd+Q still works.

        view = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label='View', menu=view)
        view.add_command(label='Log file',
                         command=lambda: Logs.view(filepath=Logs.LOGFILE, tk_obj=app),
                         # MacOS: can't display 'Cmd+L' b/c won't override native cmd.
                         accelerator='Ctrl+L')
        view.add_command(label='Plot of log data',
                         command=lambda: Logs.analyze_logfile(do_plot=True),
                         accelerator='Ctrl+Shift+P')
        view.add_command(label='Analysis of log data',
                         command=lambda: Logs.show_analysis(tk_obj=app),
                         accelerator='Ctrl+Shift+L')
        view.add_command(label='Saved Analyses',
                         command=lambda: Logs.view(Logs.ANALYSISFILE, tk_obj=app),
                         accelerator='Ctrl+Shift+A')

        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label='Help', menu=help_menu)
        help_menu.add_command(label='Information',
                              command=self.share.info)
        help_menu.add_command(label='Compliment',
                              command=self.share.compliment,
                              accelerator='Ctrl+Shift+C')
        help_menu.add_command(label='File paths',
                              command=lambda: self.share.filepaths(window=app))
        help_menu.add_command(label='Test example data',
                              command=lambda: Logs.show_analysis(tk_obj=app, do_test=True))

        help_menu.add_command(label='About',
                              command=self.share.about)

        # For Button constructors, self.master is implicit as the parent.
        self.share.viewlog_b = ttk.Button(
            text='View log file',
            command=lambda: Logs.view(Logs.LOGFILE, tk_obj=app),
            takefocus=False)
        # Set interval & summary focus button attributes with *.share.* b/c need
        #   to reconfigure them in Modeler.
        # starting_b will be replaced with an active ttk intvl_b after first
        #   interval completes; it is re-gridded in interval_data().
        # starting_b is tk.B b/c ttk.B doesn't use disabledforeground keyword.
        self.share.starting_b = tk.Button(
            text='Starting data', width=18,
            disabledforeground='grey10', state=tk.DISABLED,
            takefocus=False)
        self.share.intvl_b = ttk.Button(
            text='Interval data', width=18,
            command=self.emphasize_intvl_data,
            takefocus=False)
        self.share.sumry_b = ttk.Button(
            text='Summary data', width=20,
            command=self.emphasize_sumry_data,
            takefocus=False)

    def master_layout(self) -> None:
        """
        Master and dataframe configuration, keybindings, row headers,
        separators, and grids.
        """

        # OS-specific window size ranges set in Controller __init__
        # Need to color in all the master Frame and use near-white border;
        #   bd changes to darker shade for click-drag and loss of focus.
        self.master.config(bg=self.master_bg,
                           highlightthickness=3,
                           highlightcolor='grey95',
                           highlightbackground='grey75'
                           )
        # Need to provide exit info to Terminal and log.
        self.master.protocol('WM_DELETE_WINDOW', lambda: utils.quit_gui(mainloop=app))

        self.master.bind_all('<Escape>', lambda _: utils.quit_gui(mainloop=app))
        self.master.bind('<Control-q>', lambda _: utils.quit_gui(mainloop=app))
        # ^^ Note: macOS Command-q will quit program without utils.quit_gui info msg.

        # Note: Toplevel key bindings are set with module binds.keyboard().
        self.master.bind('<Control-l>',
                         lambda _: Logs.view(filepath=Logs.LOGFILE, tk_obj=app))
        self.master.bind('<Shift-Control-P>',
                         lambda _: Logs.analyze_logfile(do_plot=True))
        self.master.bind('<Shift-Control-L>',
                         lambda _: Logs.show_analysis(tk_obj=app))
        self.master.bind('<Shift-Control-A>',
                         lambda _: Logs.view(filepath=Logs.ANALYSISFILE, tk_obj=app))
        self.master.bind('<Shift-Control-C>', lambda _: self.share.compliment())

        # Need to specify Ctrl-a for Linux b/c in tkinter that key is
        #   bound to the tkinter predefined virtual event <<LineStart>>,
        #   not <<SelectAll>>, for some reason? And  Shift-Control-A
        #   will select text from cursor to <<LineStart>>.
        if const.MY_OS in 'lin':
            def select_all():
                app.focus_get().event_generate('<<SelectAll>>')

            self.master.bind_all('<Control-a>', lambda _: select_all())

            def select_none():
                app.focus_get().event_generate('<<SelectNone>>')

            self.master.bind_all('<Shift-Control-A>', lambda _: select_none())

        # Theme controls entire window theme, but only for ttk.Style objects.
        # Options: classic, alt, clam, default, aqua(MacOS only)
        ttk.Style().theme_use('alt')

        self.master.columnconfigure(1, weight=1)
        self.master.columnconfigure(2, weight=1)

        self.dataframe.configure(borderwidth=3, relief='sunken',
                                 bg=self.data_bg)
        self.dataframe.grid(row=2, column=1, rowspan=7, columnspan=2,
                            padx=(5, 10), sticky=tk.NSEW)
        self.dataframe.columnconfigure(1, weight=1)
        self.dataframe.columnconfigure(2, weight=1)

        # Fill in headers for all data rows.
        #   Row 2 needs separate configuration and grid padding.
        row_header = {
            'Count interval, t': 3,
            '# tasks reported': 4,
            'Task times:  avg': 5,
            'stdev': 6,
            'range': 7,
            'total': 8,
            'Interval datetime:': 10,
            'Next count in:': 11,
            'Tasks in queue:': 12,
            'Notices:': 13
        }

        for header, rownum in row_header.items():
            tk.Label(text=f'{header}',
                     bg=self.master_bg,
                     fg=self.share.row_fg
                     ).grid(row=rownum, column=0,
                            padx=(5, 0), pady=(0, 1),
                            sticky=tk.NE)
            # ^^ Grid to N or NE to prevent Notices label from shifting down
            #    when more than one row of update_notice_text() text appears.
            #    For all Label constructors, self.master parent is implicit.

        # Pady first row to better align headers with data in dataframe.
        tk.Label(text='Counting since',
                 bg=self.master_bg,
                 fg=self.share.row_fg
                 ).grid(row=2, column=0,
                        padx=(5, 0), pady=(3, 0),
                        sticky=tk.NE)

        # Need to accommodate cases of two headers in same row.
        tk.Label(text='Summary dt:',
                 bg=self.master_bg,
                 fg=self.share.row_fg
                 ).grid(row=10, column=2, sticky=tk.W)
        tk.Label(text='Counts until exit:',
                 bg=self.master_bg,
                 fg=self.share.row_fg
                 ).grid(row=12, column=2, sticky=tk.W)

        # For colored separators, use ttk.Frame instead of ttk.Separator.
        # Initialize then configure style for separator color.
        style_sep = ttk.Style()
        style_sep.configure(style='Sep.TFrame', background=self.master_bg)
        sep1 = ttk.Frame(style='Sep.TFrame', relief="raised", height=6)
        sep2 = ttk.Frame(style='Sep.TFrame', relief="raised", height=6)

        # %%%%%%%%%%%%%%%%%%% grid: sorted by row number %%%%%%%%%%%%%%%%%%%%%%
        self.share.viewlog_b.grid(
            row=0, column=0, padx=5, pady=(8, 4))
        self.share.starting_b.grid(
            row=0, column=1, padx=(16, 0), pady=(6, 4))
        self.share.sumry_b.grid(
            row=0, column=2, padx=(0, 20), pady=(8, 4))
        sep1.grid(
            row=1, column=0, columnspan=5, padx=5, pady=(2, 5), sticky=tk.EW)
        self.time_start_l.grid(  # No padx + sticky EW = centered.
            row=2, column=1, columnspan=2, sticky=tk.EW)
        self.interval_t_l.grid(
            row=3, column=1, padx=(10, 8), sticky=tk.EW)
        self.summary_t_l.grid(
            row=3, column=2, padx=(0, 12), sticky=tk.EW)
        self.task_count_l.grid(
            row=4, column=1, padx=12, sticky=tk.EW)
        self.task_count_sumry_l.grid(
            row=4, column=2, padx=(0, 12), sticky=tk.EW)
        self.taskt_avg_l.grid(
            row=5, column=1, padx=12, sticky=tk.EW)
        self.taskt_mean_sumry_l.grid(
            row=5, column=2, padx=(0, 12), sticky=tk.EW)
        self.taskt_sd_l.grid(
            row=6, column=1, padx=12, sticky=tk.EW)
        self.taskt_sd_sumry_l.grid(
            row=6, column=2, padx=(0, 12), sticky=tk.EW)
        self.taskt_range_l.grid(
            row=7, column=1, padx=12, sticky=tk.EW)
        self.taskt_range_sumry_l.grid(
            row=7, column=2, padx=(0, 12), sticky=tk.EW)
        self.taskt_total_l.grid(
            row=8, column=1, padx=12, sticky=tk.EW)
        self.taskt_total_sumry_l.grid(
            row=8, column=2, padx=(0, 12), sticky=tk.EW)
        sep2.grid(
            row=9, column=0, columnspan=5, padx=5, pady=(6, 6), sticky=tk.EW)
        self.time_prev_cnt_l.grid(
            row=10, column=1, columnspan=2, padx=3, sticky=tk.W)
        self.time_prev_sumry_l.grid(
            row=10, column=2, padx=(90, 0), sticky=tk.W)
        self.time_next_cnt_l.grid(
            row=11, column=1, padx=3, sticky=tk.W)
        self.num_tasks_all_l.grid(
            row=12, column=1, padx=3, sticky=tk.W)

        # Place cycles_remain value in same cell as its header, but shifted right.
        if const.MY_OS in 'lin, dar':
            self.cycles_remain_l.grid(
                row=12, column=2, padx=(123, 0), sticky=tk.W)
        else:  # is 'win':
            self.cycles_remain_l.grid(
                row=12, column=2, padx=(110, 0), sticky=tk.W)

        # Need pady for alignment with the row header.
        self.share.notice_l.grid(
            row=13, column=1, columnspan=2, rowspan=2, padx=5, pady=(1, 0), sticky=tk.NW)
        self.share.compliment_l.grid(
            row=14, column=1, columnspan=2, padx=5, sticky=tk.EW)

        # Some control variables have default or initial start values,
        #   so make labels invisible in pre-settings dataframe by matching
        #   them to the background color.
        self.interval_t_l.config(foreground=self.data_bg)
        self.summary_t_l.config(foreground=self.data_bg)
        self.task_count_l.config(foreground=self.data_bg)
        self.task_count_sumry_l.config(foreground=self.data_bg)

    def settings(self) -> None:
        """
        Configures the Toplevel window that appears at startup.
        Confirms default parameters or sets new ones for count and
        summary interval times, counting limit, and log file option.
        """
        # Toplevel window basics
        self.settings_win.title('Set run settings')
        self.settings_win.resizable(width=False, height=False)
        self.settings_win.config(relief='raised', bg=self.master_bg,
                                 highlightthickness=3,
                                 highlightcolor=self.share.highlight,
                                 highlightbackground=self.deemphasize)

        # Need to make settings window topmost to place it above the
        #   app window.
        if const.MY_OS in 'lin, win':
            self.settings_win.attributes('-topmost', True)
        # In macOS, topmost places Combobox selections BEHIND the window,
        #    but focus_force() makes it visible; must be a tkinter bug?
        else:  # is 'dar':
            self.settings_win.focus_force()

        settings_style = ttk.Style()
        settings_style.configure('Set.TLabel', background=self.master_bg,
                                 foreground=self.share.row_fg)

        # Need text in master window to prompt user to enter settings.
        #   The message text may be covered by the settings_win, but is
        #   seen if user drags settings_win away.
        self.time_start_l.configure(text='Waiting for run settings...')

        # Inner functions for window and selection control and user FYI:

        # Need to disable default window Exit; only allow exit from active
        #   Confirm button.
        def no_exit_on_x():
            messagebox.showinfo(
                parent=self.settings_win,
                title='Invalid exit',
                detail='"Count now" button closes window and begins'
                       ' counting. Or you can quit program from the main'
                       ' window (or "Esc" key) without starting counts.')

        self.settings_win.protocol('WM_DELETE_WINDOW', no_exit_on_x)

        def update_intvl():
            self.share.intvl_choice['values'] = sumry_unit[self.share.sumry_unit_choice.get()]

        def update_sumry_unit():
            self.share.sumry_unit_choice['values'] = interval_t[self.share.intvl_choice.get()]

        # Settings widget construction and configurations.
        intvl_label = ttk.Label(self.settings_win, text='Count time interval',
                                style='Set.TLabel')
        interval_t = {'1h': ('day', 'hr'),
                      '30m': ('day', 'hr'),
                      '20m': ('hr', 'min'),
                      '15m': ('hr', 'min'),
                      '10m': ('hr', 'min'),
                      }
        self.share.intvl_choice.configure(
            state='readonly', width=4, height=5,
            textvariable=self.share.setting['interval_t'],
            values=tuple(interval_t.keys()))
        self.share.intvl_choice.bind(
            '<<ComboboxSelected>>', lambda _: update_sumry_unit())
        self.share.setting['interval_t'].set(self.share.intvl_choice.get())

        sumry_label1 = ttk.Label(
            self.settings_win, text='Summary interval: time value',
            style='Set.TLabel')
        self.sumry_value_entry.configure(
            validate='key', width=4,
            textvariable=self.share.setting['sumry_t_value'],
            validatecommand=(
                self.sumry_value_entry.register(utils.enter_only_digits), '%P', '%d'))

        sumry_label2 = ttk.Label(
            self.settings_win, text='time unit', style='Set.TLabel')
        sumry_unit = {'day': ('1h', '30m'),
                      'hr': ('30m', '20m', '15m', '10m'),
                      'min': ('20m', '15m', '10m')
                      }
        self.share.sumry_unit_choice.configure(
            state='readonly', width=4,
            textvariable=self.share.setting['sumry_t_unit'],
            values=tuple(sumry_unit.keys()))
        self.share.sumry_unit_choice.bind(
            '<<ComboboxSelected>>', lambda _: update_intvl())
        self.share.setting['sumry_t_unit'].set(self.share.sumry_unit_choice.get())

        # Specify number limit of counting cycles to run.
        cycles_label = ttk.Label(self.settings_win, text='# Count cycles',
                                 style='Set.TLabel')
        self.cycles_max_entry.configure(
            validate='key', width=4,
            textvariable=self.share.setting['cycles_max'],
            validatecommand=(
                self.cycles_max_entry.register(utils.enter_only_digits), '%P', '%d'))

        # Provide user options for logging results to file and using auto-update.
        log_label = ttk.Label(self.settings_win,
                              text='Log results to file',
                              style='Set.TLabel')
        self.log_choice.configure(variable=self.share.setting['do_log'],
                                  bg=self.master_bg, borderwidth=0)

        beep_label = ttk.Label(self.settings_win,
                               text='No tasks running alarm',
                               style='Set.TLabel')
        self.beep_choice.configure(variable=self.share.setting['sound_beep'],
                                   bg=self.master_bg, borderwidth=0)

        default_button = ttk.Button(self.settings_win, text='Use defaults',
                                    command=self.share.defaultsettings)
        self.countnow_button.configure(text='Count now',
                                       command=self.start_when_confirmed)

        # Grid settings widgets; generally sorted by row.
        intvl_label.grid(row=0, column=0, padx=5, pady=10, sticky=tk.E)
        self.share.intvl_choice.grid(row=0, column=1)
        default_button.grid(row=0, column=3, padx=10, pady=(10, 0), sticky=tk.E)
        sumry_label1.grid(row=1, column=0, padx=(10, 5), pady=10, sticky=tk.E)
        self.sumry_value_entry.grid(row=1, column=1)
        sumry_label2.grid(row=1, column=2, padx=5, pady=10, sticky=tk.E)
        self.share.sumry_unit_choice.grid(row=1, column=3, padx=5, pady=10, sticky=tk.W)
        cycles_label.grid(row=2, column=0, padx=5, pady=10, sticky=tk.E)
        self.cycles_max_entry.grid(row=2, column=1)
        log_label.grid(row=3, column=0, padx=5, pady=5, sticky=tk.E)
        self.log_choice.grid(row=3, column=1, padx=0, pady=5, sticky=tk.W)
        beep_label.grid(row=5, column=0, padx=5, pady=0, sticky=tk.E)
        self.beep_choice.grid(row=5, column=1, padx=0, pady=0, sticky=tk.W)
        self.countnow_button.grid(
            row=5, column=3, padx=10, pady=(0, 10), sticky=tk.E)

    def settings_tooltips(self) -> None:
        """
        Calls to Tooltips module, for mouseover of info Button icons, to
        explain usage of entries and selections in the settings window.
        """

        # Need to use ttk.Button and styles on macOS to avoid square button img.
        #  Provides the same look on Linux, Windows, macOS. For Linux and
        #  Windows, works the same as tk.Button if configure with same options.
        _s = ttk.Style()
        _s.configure(style='Tooltip.TButton',
                     image=self.info_button_img,
                     background=self.master_bg,
                     highlightthickness=0,
                     highlightcolor=self.master_bg,
                     highlightbackground=self.master_bg,
                     activebackground=self.master_bg
                     )
        _s.map(style='Tooltip.TButton',
               background=[('pressed', '!focus', self.master_bg),
                           ('active', self.master_bg)],
               relief=[('pressed', tk.FLAT),
                       ('!pressed', tk.FLAT)]
               )
        intvl_tip_btn = ttk.Button(
            self.settings_win, style='Tooltip.TButton', takefocus=False)
        cycles_tip_btn = ttk.Button(
            self.settings_win, style='Tooltip.TButton', takefocus=False)
        beep_tip_btn = ttk.Button(
            self.settings_win, style='Tooltip.TButton', takefocus=False)

        intvl_tip_txt = (
            'If the desired pull-down time values do not appear, then'
            ' either select a different summary time (or a different'
            ' interval time if do not see a desired summary time unit)'
            ' or click "Use defaults" and try again.')
        cycles_tip_txt = (
            'Interval counting stops after number of cycles'
            ' entered. Enter 0 (zero) for a one-off status report.')

        # If change the beep interval, then also change it in update_notice_text()
        #   for no tasks running condition.
        beep_interval = const.NOTICE_INTERVAL * 4
        beep_tip_txt = (
            f'Provide an audible notification when no tasks are running'
            ' because tasks or Project are suspended by user or because'
            ' of an unexpected event. Occurs after the first full'
            ' interval cycle elapses with no tasks running; beeps then'
            f' occur every {beep_interval} seconds.')

        utils.Tooltip(widget=intvl_tip_btn, tt_text=intvl_tip_txt)
        utils.Tooltip(widget=cycles_tip_btn, tt_text=cycles_tip_txt)
        utils.Tooltip(widget=beep_tip_btn, tt_text=beep_tip_txt)

        # Need OS-specific grids for proper padding and alignments:
        if const.MY_OS == 'lin':
            intvl_tip_btn.grid(row=0, column=0, padx=(50, 0), sticky=tk.W)
            cycles_tip_btn.grid(row=2, column=0, padx=(75, 0), sticky=tk.W)
            beep_tip_btn.grid(row=5, column=0, padx=(15, 0), sticky=tk.W)
        elif const.MY_OS == 'win':
            intvl_tip_btn.grid(row=0, column=0, padx=(45, 0), sticky=tk.W)
            cycles_tip_btn.grid(row=2, column=0, padx=(110, 0), sticky=tk.W)
            beep_tip_btn.grid(row=5, column=0, padx=(35, 0), sticky=tk.W)
        else:  # is 'dar'
            intvl_tip_btn.grid(row=0, column=0, padx=(35, 0), sticky=tk.W)
            cycles_tip_btn.grid(row=2, column=0, padx=(60, 0), sticky=tk.W)
            beep_tip_btn.grid(row=5, column=0, padx=(10, 0), sticky=tk.W)

    def confirm_settings(self) -> bool:
        """
        Confirm validity of summary and interval times,
        set all to valid control variable dictionary values,
        and set up logging of data, if optioned.
        Called from start_when_confirmed().

        :return: True if settings are all valid.
        """
        # Need to set to True when interval and summary times are
        #   confirmed as valid. All other settings are self-validating.
        good_settings = False

        # Note: self.share.setting['interval_t'] and self.sumry_t_value
        #    are set in settings() or in Modeler.default_settings().
        if not self.share.setting['interval_t'].get():
            self.share.defaultsettings()

        if self.share.setting['interval_t'].get() != '1h':
            interval_m = int(self.share.setting['interval_t'].get()[:-1])
        else:
            # Need to convert 1h to minutes for comparisons.
            interval_m = 60

        self.share.setting['interval_m'].set(interval_m)

        if not self.share.setting['sumry_t_value'].get():
            _m = "Summary value cannot be blank. A default of '1' will be used."
            messagebox.showerror(title='Invalid entry',
                                 detail=_m,
                                 parent=self.settings_win)
            self.share.setting['sumry_t_value'].set(1)

        # If sumry_value = 0, it will be caught by interval_m comparison below.
        sumry_value = self.share.setting['sumry_t_value'].get()

        # Need to set summary_t here as concat of the two sumry_t element strings,
        #   then convert it to minutes for use in comparisons.
        summary_t = f"{sumry_value}{self.share.sumry_unit_choice.get()[:1]}"
        self.share.setting['summary_t'].set(summary_t)

        summary_m = times.string_to_min(summary_t)

        if interval_m >= summary_m or summary_m % interval_m != 0:
            info = "Summary time must be greater than, and a multiple of, interval time"
            messagebox.showerror(title='Invalid entry',
                                 detail=info,
                                 parent=self.settings_win)
            # Need to offer user valid alternatives to bad times entered.
            if self.share.setting['sumry_t_unit'].get() == 'min':
                self.share.setting['sumry_t_value'].set(2 * interval_m)
            elif self.share.setting['sumry_t_unit'].get() == 'hr':
                self.share.setting['sumry_t_value'].set(2 * sumry_value)
        elif interval_m < summary_m and summary_m % interval_m == 0:
            good_settings = True

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

        # Need to set initial cycles_remain to cycles_max.
        self.share.data['cycles_remain'].set(self.share.setting['cycles_max'].get())

        # Note: logging module is used only to lazily manage the data log file.
        if self.share.setting['do_log'].get():
            logging.basicConfig(filename=str(Logs.LOGFILE),
                                level=logging.INFO,
                                filemode="a",
                                format='%(message)s')
        else:
            app.title(f'Count BOINC tasks on {gethostname()}'
                      ' (not logging data)')

        # Need to provide a unique name of app window for concurrent instances.
        if good_settings and not self.share.setting['do_log'].get():
            app.title(f'Count BOINC tasks on {gethostname()}'
                      f' (Not logging data)')

        return good_settings

    def start_when_confirmed(self) -> None:
        """
        Main gatekeeper for settings().
        Calls confirm_settings(); if all is good then starts threads,
        calls emphasize_start_data(), and closes settings() window,
        which ends the startup sequence.
        Called from settings() countnow_button.
        """
        # Either run a 1-off status report or begin interval counts:
        if self.confirm_settings():
            if self.share.setting['cycles_max'].get() == 0:
                self.share.data['cycles_remain'].set(0)
                self.share.setting['interval_t'].set('DISABLED')
                self.share.setting['summary_t'].set('DISABLED')
                self.share.notice['notice_txt'].set('STATUS REPORT ONLY')
            else:
                self.start_threads()

            self.emphasize_start_data()
            self.share.startdata('start')
            self.settings_win.destroy()

    def start_threads(self) -> None:
        """
        Set up and start threads for intervals, notices, and logging.
        Called from start_when_confirmed() as part of startup sequence.
        """
        # There are no thread.join(), so use daemon for clean exits.
        intvl_thread = threading.Thread(
            target=self.share.intervaldata, daemon=True)

        notice_thread = threading.Thread(
            target=self.share.taskstatenotices, daemon=True)

        log_thread = threading.Thread(
            target=self.share.logit, daemon=True, args=(None,))

        intvl_thread.start()
        notice_thread.start()
        log_thread.start()

    def emphasize_start_data(self) -> None:
        """
        Config data labels in master window for starting data emphasis.
        Establish start time.
        Called from start_when_confirmed() from 'Count now' button.
        """
        time_start = datetime.now().strftime(const.SHORT_FMT)
        self.time_start_l.config(text=time_start)
        self.share.long_time_start = datetime.now().strftime(const.LONG_FMT)

        # Need to keep sumry_b button disabled until after 1st summary interval.
        self.share.sumry_b.config(state=tk.DISABLED)

        self.interval_t_l.config(foreground=self.emphasize)
        self.summary_t_l.config(foreground=self.deemphasize)
        self.task_count_l.config(foreground=self.share.highlight)

        self.taskt_avg_l.configure(foreground=self.share.highlight)
        self.taskt_sd_l.configure(foreground=self.emphasize)
        self.taskt_range_l.configure(foreground=self.emphasize)
        self.taskt_total_l.configure(foreground=self.emphasize)

        self.task_count_sumry_l.configure(foreground=self.deemphasize)
        self.taskt_mean_sumry_l.configure(foreground=self.deemphasize)
        self.taskt_sd_sumry_l.configure(foreground=self.deemphasize)
        self.taskt_range_sumry_l.configure(foreground=self.deemphasize)
        self.taskt_total_sumry_l.configure(foreground=self.deemphasize)

        if not self.share.setting['do_log'].get():
            self.share.viewlog_b.configure(style='View.TButton', state=tk.DISABLED)

        if self.share.setting['cycles_max'].get() > 0:
            self.starting_tooltips()

    def starting_tooltips(self):
        """
        Provide mouseover tooltips for data emphasis buttons.
        Tips will not be active once the first interval posts.
        """

        starting_tip_txt = (
            'This data column is now showing task data retrieved'
            ' from the most recent boinc-client report before'
            f' {PROGRAM_NAME} started. Once the first count'
            ' interval time has elapsed, data for that interval will'
            ' display and this button will become "Interval data".'
        )
        utils.Tooltip(widget=self.share.starting_b, tt_text=starting_tip_txt)

        summary_tip_txt = (
            'This button will activate and allow switching of visual'
            ' emphasis between interval and summary data columns'
            ' once the first summary count interval time has elapsed.'
        )
        utils.Tooltip(widget=self.share.sumry_b, tt_text=summary_tip_txt)

    def emphasize_intvl_data(self) -> None:
        """
        Switches font emphasis from Summary data to Interval data.
        Called from 'Interval data' button.
        """

        self.interval_t_l.config(foreground=self.emphasize)
        self.summary_t_l.config(foreground=self.deemphasize)

        # Interval data, column1
        self.task_count_l.configure(foreground=self.share.highlight)
        self.taskt_avg_l.configure(foreground=self.share.highlight)
        self.taskt_sd_l.configure(foreground=self.emphasize)
        self.taskt_range_l.configure(foreground=self.emphasize)
        self.taskt_total_l.configure(foreground=self.emphasize)

        # Summary data, column2, de-emphasize font color
        self.task_count_sumry_l.configure(foreground=self.deemphasize)
        self.taskt_mean_sumry_l.configure(foreground=self.deemphasize)
        self.taskt_sd_sumry_l.configure(foreground=self.deemphasize)
        self.taskt_range_sumry_l.configure(foreground=self.deemphasize)
        self.taskt_total_sumry_l.configure(foreground=self.deemphasize)

    def emphasize_sumry_data(self) -> None:
        """
        Switches font emphasis from Interval data to Summary data.
        Called from 'Summary data' button.
        """
        self.interval_t_l.config(foreground=self.deemphasize)
        self.summary_t_l.config(foreground=self.emphasize)

        # Interval data, column1, de-emphasize font color
        self.task_count_l.configure(foreground=self.deemphasize)
        self.taskt_avg_l.configure(foreground=self.deemphasize)
        self.taskt_sd_l.configure(foreground=self.deemphasize)
        self.taskt_range_l.configure(foreground=self.deemphasize)
        self.taskt_total_l.configure(foreground=self.deemphasize)

        # Summary data, column2, emphasize font color
        self.task_count_sumry_l.configure(foreground=self.share.highlight)
        self.taskt_mean_sumry_l.configure(foreground=self.share.highlight)
        self.taskt_sd_sumry_l.configure(foreground=self.emphasize)
        self.taskt_range_sumry_l.configure(text=self.share.data['taskt_range'].get(),
                                           foreground=self.emphasize)
        self.taskt_total_sumry_l.configure(foreground=self.emphasize)

    def app_got_focus(self, focus_event) -> None:
        """Give menu bar headings normal color when app has focus.

        :param focus_event: Implicit event passed from .bind_all()
        """
        self.menubar.entryconfig("File", foreground='black', state=tk.NORMAL)
        self.menubar.entryconfig("View", foreground='black', state=tk.NORMAL)
        self.menubar.entryconfig("Help", foreground='black', state=tk.NORMAL)
        self.view_button_style.configure('View.TButton', foreground='black',
                                         background='grey75')
        if self.share.setting['do_log'].get():
            self.share.viewlog_b.configure(style='View.TButton', state=tk.NORMAL)
        return focus_event

    def app_lost_focus(self, focus_event) -> None:
        """Give menu bar headings grey-out color when app looses focus.

        :param focus_event: Implicit event passed from .bind_all()
        """
        self.menubar.entryconfig("File", foreground='grey', state=tk.DISABLED)
        self.menubar.entryconfig("View", foreground='grey', state=tk.DISABLED)
        self.menubar.entryconfig("Help", foreground='grey', state=tk.DISABLED)
        self.view_button_style.configure('View.TButton', foreground='grey')
        self.share.viewlog_b.configure(style='View.TButton', state=tk.DISABLED)
        return focus_event


# ##################### User information methods #######################
class CountFyi:
    """
    Methods to provide user with information and help.
    """

    def __init__(self, share):
        self.share = share

    @staticmethod
    def about() -> None:
        """
        Toplevel display of program metadata.
        Called from Viewer.master_widgets() Help menu bar.
        """
        # Have highlightcolor match self.master_bg of the app main window.
        aboutwin = tk.Toplevel(highlightthickness=5,
                               highlightcolor='SteelBlue4',
                               highlightbackground='grey75')
        aboutwin.geometry(utils.position_wrt_window(window=app))
        aboutwin.resizable(width=False, height=False)
        aboutwin.title(f'About {PROGRAM_NAME}')
        aboutwin.focus_set()

        insert_txt = utils.about_text()

        max_line = len(max(insert_txt.splitlines(), key=len))

        abouttxt = tk.Text(aboutwin,
                           font='TkFixedFont',
                           width=max_line,
                           height=insert_txt.count('\n') + 2,
                           relief='groove',
                           borderwidth=5,
                           padx=25)
        abouttxt.insert(1.0, insert_txt)
        abouttxt.pack()
        # Need to not have cursor appear in Text, but allow
        #   rt-click edit commands to work if needed.
        abouttxt.configure(state=tk.DISABLED)

        binds.keybind('close', aboutwin)
        binds.click('right', abouttxt)

    def compliment_me(self) -> None:
        """A silly diversion; called from Help menu bar and keybinding.
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
            'Congratulations!', 'Try not. Do or do not. There is no try.',
            "Well, THAT's impressive.", 'I hear that you are the one.',
            'You excel at everything.', 'Your voice is very soothing.',
            'Is it true what people say?', 'The word is, you got it!',
            'The Nobel Committee has been trying to reach you.',
            'The Academy is asking for your CV.', 'You look great!',
            'The President seeks your council.', 'Thank you so much!',
            'The Prime Minister seeks your council.', 'Crunchers rule!',
            'Crunchers are the best sort of people.',
            'What you did takes an incredible amount of courage.',
            'Your ability to accomplish your goals is impressive.',
            'You are incredibly talented.',
            'You are so passionate and full of energy.',
            'You are the best role model.',
            'You have an incredible sense of humor.',
            'You have a beautiful smile.',
            'You are an excellent problem solver.',
            'You have a unique sense of style.',
            'You always know how to put together the perfect outfit.',
            "I can't think of anything to say. Sorry.",
        ]
        self.share.compliment_l.config(text=choice(compliments))
        self.share.notice_l.grid_remove()
        # Need to re-grid initial master_widgets() grids b/c its grid may
        #   have been removed by a notice_l call. Original grid coordinates
        #   are set in master_widgets().
        self.share.compliment_l.grid()

        def refresh():
            self.share.compliment_l.grid_remove()
            # Re-grid notice to return to current Notice text.
            self.share.notice_l.grid()
            app.update_idletasks()

        self.share.compliment_l.after(4444, refresh)

    @staticmethod
    def file_paths(window: tk.Toplevel) -> None:
        """
        Toplevel display of full paths for program-generated files.

        :param window: The tk Toplevel window object over which this
            Toplevel is to appear.
        """

        # The *window* parameter is used here, but not in other Fyi methods,
        #   b/c file_paths() is called from toplevels other than just
        #   the app main window.

        # Have highlightcolor match self.master_bg of the app main window.
        pathswin = tk.Toplevel(highlightthickness=5,
                               highlightcolor='SteelBlue4',
                               highlightbackground='grey75')

        # Need to position window over the window from which it is called.
        pathswin.geometry(utils.position_wrt_window(window=window))
        pathswin.resizable(False, False)
        pathswin.title(f'Program-generated files on {gethostname()}')
        pathswin.focus_set()

        insert_txt = (
            'Included with GitHub project distribution:\n\n'
            f'Example log file: (file exists: {Path.exists(Logs.EXAMPLELOG)})\n'
            f'   {Logs.EXAMPLELOG}\n\n'
            f'Created by {PROGRAM_NAME}:\n\n'
            f'Data log (file exists: {Path.exists(Logs.LOGFILE)})\n'
            '   ...do not alter this file while program is running\n'
            f'   {Logs.LOGFILE}\n\n'
            f'Saved log analyses (file exists: {Path.exists(Logs.ANALYSISFILE)})\n'
            f'   {Logs.ANALYSISFILE}\n'
        )

        # Need to add OS-specific instance management file path.
        if const.MY_OS == 'win':
            insert_txt = (f'{insert_txt}\nSentinel file for this instance'
                          f' (is deleted on exit)\n'
                          f'   {sentinel.name}\n')
        else:
            insert_txt = (f'{insert_txt}\nLockfile (hidden):\n'
                          f'   {lockfile_fullpath}\n')

        max_line = len(max(insert_txt.splitlines(), key=len))

        pathstxt = tk.Text(pathswin, font='TkFixedFont',
                           height=insert_txt.count('\n') + 1,
                           width=max_line,
                           relief='groove', borderwidth=5,
                           padx=10, pady=10)
        pathstxt.insert(1.0, insert_txt)

        # Need to center the header line.
        # pathstxt.tag_configure("header", justify='center')
        # pathstxt.tag_add("header", "1.0", "1.0")
        pathstxt.pack()

        binds.keybind('close', toplevel=pathswin)
        binds.click('right', pathstxt)

    @staticmethod
    def information() -> None:
        """
        Toplevel display of basic information for usage and actions.
        Called from Viewer.master_widgets() Help menu bar.
        """

        # Have highlightcolor match self.master_bg of the app main window.
        infowin = tk.Toplevel(highlightthickness=5,
                              highlightcolor='SteelBlue4',
                              highlightbackground='grey75')
        infowin.geometry(utils.position_wrt_window(window=app))
        infowin.resizable(False, False)
        infowin.title('Usage information')
        infowin.focus_set()

        insert_txt = ("""
        - Counting begins once "Count now" is clicked in settings window.\n
        - Interval and Summary data buttons switch visual emphasis;
                ...those buttons activate once their data post.
                The Summary task time "avg" is the weighted mean.\n
        - At start, '# tasks reported' and 'Interval time' are from
                the most recent hourly BOINC report.\n
        - Number of tasks in queue and Notices update every"""
                      f' {const.NOTICE_INTERVAL} seconds.\n'
                      """
        - Displayed countdown clock time is approximate.\n
        - Counts and Notices histories are in the log file.\n
        - While not recommended, multiple program instances can be run
                from separate directories with command line execution.
                Only one stand-alone app instance is allowed.\n
        - When analysis of logged hours is "cannot determine"...
                Quick fix: backup then delete log file, restart program.\n
        - If plotting or analysis of log data is not working, run a test
                with Help>Run example data. If that works, then the
                problem is with your log file data. (Did you edit it?)
                Quick fix: backup then delete log file, restart program.\n
        - Most common key commands work as expected.
        - Right-click actions only affect on-screen text, not file content.
                Edits in the log analysis window, such as notations,
                can be saved to the log analysis file.\n
        """)

        # OS-specific Text widths were empirically determined for TkTextFont.
        os_width = 0
        if const.MY_OS in 'lin, win':
            os_width = 64
        else:  # is 'dar'
            os_width = 56

        infotxt = tk.Text(infowin, font='TkTextFont',
                          width=os_width, height=insert_txt.count('\n') + 2,
                          relief='groove', padx=15)
        infotxt.insert(1.0, insert_txt)
        infotxt.pack()

        # Need to not have cursor appear in Text, but allow
        #   rt-click edit commands to work if needed.
        infotxt.configure(state=tk.DISABLED)

        binds.keybind('close', toplevel=infowin)
        binds.click('right', infotxt)


# ################## MVC Controller; is app mainloop ###################
class CountController(tk.Tk):
    """
    The MVC controller represents the tkinter main window and main thread.
    Other MVC Classes can interact through the Controller via the
    'share' parameter.
    Architecture based on https://stackoverflow.com/questions/32864610/.
    """

    def __init__(self):
        super().__init__()

        # Need window sizes to provide room for multi-line notices,
        #    but not get minimized enough to exclude notices row.
        # Main window sizes need to be OS-specific b/c of different
        #    default OS text font widths set in config_constants.LABEL_FONT.
        if const.MY_OS == 'lin':
            self.minsize(594, 370)
        elif const.MY_OS == 'win':
            self.minsize(800, 670)
        else:  # is 'dar':
            self.minsize(615, 390)

        CountViewer(share=self)

    def defaultsettings(self) -> None:
        """
        Starting settings of: report interval, summary interval,
        counting limit, and log file option.
        """
        CountModeler(share=self).default_settings()

    def startdata(self, called_from: str) -> None:
        """
        Is called from Viewer.startup().
        """
        CountModeler(share=self).start_data(called_from)

    def intervaldata(self) -> None:
        """
        Is called from Viewer.start_threads().
        """
        CountModeler(share=self).interval_data()

    def taskstatenotices(self) -> None:
        """
        Is called from Viewer.start_threads().
        """
        CountModeler(share=self).manage_notices()

    def logit(self, called_from: str) -> None:
        """Send data to log file.
        Is called from Viewer.start_threads()

        :param called_from: Either 'start', 'interval' or 'notice',
                            depending on type of data to be logged.
        """
        CountModeler(share=self).log_it(called_from)

    def about(self) -> None:
        """Is called from Viewer.master_widgets(), Help menu bar.
        """
        CountFyi(share=self).about()

    def compliment(self) -> None:
        """Is called from Viewer.master_widgets(), Help menu bar and
        keybind. A silly diversion.
        """
        CountFyi(share=self).compliment_me()

    def filepaths(self, window: tk.Toplevel) -> None:
        """Is called from Viewer.master_widgets(), Help menu bar.
        """
        CountFyi(share=self).file_paths(window)

    def info(self) -> None:
        """Is called from Viewer.master_widgets(), Help menu bar.
        """
        CountFyi(share=self).information()


def main():
    """Start the tkinter mainloop. app is the main window, set in __main__. """
    app.title(f'Counting BOINC tasks on {gethostname()}')
    utils.use_app_icon(app)
    print(f'{PROGRAM_NAME} now running...')
    app.mainloop()


if __name__ == "__main__":

    utils.run_checks()

    # Need to set up conditions to control multiple instances.
    # Prevent multiple instances writing to the same log file.
    # In Class Logs, LOGFILE path constants are different
    #  for stand-alone and Terminal executions.
    # Multiple instances of Terminal executions may run if launched from
    #  different directories.

    # Tkinter main window is created in CountController() class and
    #  its mainloop is called in main() function.
    if const.MY_OS == 'win':

        # Can restrict all Windows executions to one instance if
        #   "with sentinel:" is replaced with these mutex module calls.
        # winstance = instances.OneWinstance()
        # winstance.exit_twinstance(exit_text)

        # Using an exit_msg in this call will exit program here if
        #   another instance is running from the LOGFILE directory.
        # Note: sentinel_count is not currently used in main script b/c
        #    instance management is handled through instances.py module.
        sentinel, sentinel_count = instances.sentinel_or_exit(
            working_dir=Logs.LOGFILE.parent, exit_msg=utils.exit_text())

        with sentinel:
            try:
                app = CountController()
                main()
            except KeyboardInterrupt:
                utils.handle_windows_keyboard_interrupt(sentinel.name)
            except Exception as unknown:
                utils.handle_windows_unexpected_error(err_msg=unknown,
                                                sentinel_name=sentinel.name)
    else:  # is 'lin' or 'dar'
        lockfile_fullpath = Path(Logs.LOGFILE.parent,
                                 f'.{PROGRAM_NAME}_lockfile')

        # Program will exit here if another instance is running from the
        #  LOGFILE directory.
        # Do not open using a 'with' statement; it will not work as expected.
        lockfile = open(lockfile_fullpath, 'w', encoding='utf8')
        instances.lock_or_exit(lockfile, utils.exit_text())

        try:
            app = CountController()
            main()
        except KeyboardInterrupt:
            utils.handle_nix_exit()
        except Exception as unknown:
            print(f'An unexpected error: {unknown}\n')
            logging.info(unknown)
        finally:
            lockfile.close()
            lockfile_fullpath.unlink()
            sys.exit(0)
