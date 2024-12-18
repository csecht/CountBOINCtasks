"""
Methods to analyze and view BOINC task data logged to file.

Class Logs, functions: analyze_logfile, plot_data, plot_data_toggle,
                       plot_display, show_analysis, uptime
Functions: close_plots

"""
# Copyright (C) 2021-2024 C. Echt under GNU General Public License'


import sys
import tkinter as tk
from pathlib import Path
from re import search, findall, MULTILINE
from socket import gethostname
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

try:
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    import matplotlib.ticker as tck
    import matplotlib.backends.backend_tkagg as backend
except (ImportError, ModuleNotFoundError) as err:
    print('Task time plots not available; A needed module was not found.\n'
          'Try installing Matplotlib the command:\n'
          ' python3 -m pip install -U matplotlib\n'
          ' ...or, depending on system: python -m pip install -U matplotlib'
          f'Error msg: {err}\n\n'
          'If the Error message mentions PIL, then install the Pillow module:\n'
          '   python3 -m pip install -U pillow.')

import count_modules as CMod
from count_modules import (bind_this as Binds,
                           files as Files,
                           instances,
                           times as T,
                           utils as Utils)

PROGRAM_NAME = instances.program_name()
MY_OS = sys.platform[:3]

# Datetime string formats used in logging and analysis reporting.
LONG_STRFTIME = '%Y-%b-%d %H:%M:%S'
SHORT_STRFTIME = '%Y %b %d %H:%M'

# Colors used for Matplotlib plots. Default marker color 'blue' is '#bfd1d4',
#   similar to X11 SteelBlue4 or DodgerBlue4 used by tkinter.
MARKER_COLOR2 = 'deepskyblue' # DeepSkyBlue, '#00bfff'
MARKER_COLOR3 = 'orange'
LIGHT_COLOR = '#d9d9d9'  # X11 gray85; X11 gray80 '#cccccc'
DARK_BG = '#333333'  # X11 gray20


def close_plots(window: tk.Toplevel) -> None:
    """
    Explicitly close all matplotlib objects and their parent tk window
    when the user closes the plot window with the system's built-in
    close window icon ("X").
    This is required to cleanly exit and close the thread running
    Matplotlib.

    :param window: The parent window being closed with a click on X.
    """
    plt.close('all')
    window.destroy()


class Logs:
    """
    Methods to analyze and view task data logged to file.
    File paths are defined as Class attribute constants.
    """

    # Need to write log files to current working directory unless program
    #   is run from a PyInstaller frozen executable, then write to Home
    #   directory. Frozen executable paths need to be absolute paths.
    DO_TEST = False
    EXAMPLELOG = Path(Path.cwd(), 'example_log.txt')
    LOGFILE = Path(Path.cwd(), f'{PROGRAM_NAME}_log.txt').resolve()
    ANALYSISFILE = Path(Path.cwd(), f'{PROGRAM_NAME}_analysis.txt').resolve()

    if getattr(sys, 'frozen', False):
        LOGFILE = Path(Path.home(), f'{PROGRAM_NAME}_log.txt').resolve()
        ANALYSISFILE = Path(Path.home(), f'{PROGRAM_NAME}_analysis.txt').resolve()

    @classmethod
    def analyze_logfile(cls, do_plot=False, do_test=False) -> tuple:
        """
        Reads log file and analyses Summary and Interval counts.
        Called from cls.show_analysis() when need to show results.
        Called from master menu or keybinding when need to plot times.

        :param do_plot: When True, call plot_data();
            USE: analyze_logfile(do_plot=True).
        :param do_test: When True, flags calls to plot_data() and from
            show_analysis() for running tests with example data that is
            provided, via the Project repository, in example_log.txt.
        :return: Text strings to display in show_analysis() Toplevel.
        """

        cls.DO_TEST = do_test
        sumry_dates = []
        sumry_intvl_vals = []
        num_sumry_intvl_vals = 0
        sumry_counts = []
        sumry_cnt_avg = 0.0
        sumry_cnt_range = ''

        intvl_dates = []
        intvl_counts = []
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
            logtext: str = Path(cls.LOGFILE).read_text(encoding='utf-8')
        except FileNotFoundError:
            info = (f'On {gethostname()}, missing necessary file:\n{cls.LOGFILE}\n'
                    'Was the settings "log results" option used?\n'
                    'Was the log file deleted, moved or renamed?')
            messagebox.showerror(title='FILE NOT FOUND', detail=info)

            return '', ''

        if cls.DO_TEST:
            try:
                logtext: str = Path(cls.EXAMPLELOG).read_text(encoding='utf-8')
                texthash: int = Utils.verify(logtext)
                if texthash != 4006408145:  # As of 06:41 4 June 2022.
                    msg = (f'Content of {cls.EXAMPLELOG} has changed, so'
                           ' the test may not work. If not working, reinstall'
                           f' the example file from {CMod.__project_url__}')
                    messagebox.showinfo(title='EXAMPLE LOG DATA MAY BE CORRUPT',
                                        detail=msg)
                do_plot = True
            except FileNotFoundError:
                info = (f'Missing example file:\n{cls.EXAMPLELOG}\n'
                        'Was the log file deleted, moved or renamed?\n'
                        f'Try reinstalling it from {CMod.__project_url__}.')
                messagebox.showerror(title='FILE NOT FOUND', detail=info)

        # Regex is based on this structure used in CountModeler.log_it():
        """
        2021-Dec-21 06:27:18; Tasks reported in the past 1h: 18
                              Task Time: avg 00:21:35,
                                         range [00:21:20 -- 00:21:54],
                                         stdev 00:00:11, total 06:28:45
                              Total tasks in queue: 53
                              984 counts remain.
        2021-Dec-21 06:27:18; >>> SUMMARY: Task count for the past 1d: 402
                              Task Time: mean 0:21:28,
                                         range [00:16:03 -- 00:22:33],
                                         stdev 00:00:42, total 5d 23:54:05
        """
        found_sumrys: list = findall(
            r'^(.*); >>> SUMMARY: .+ (\d+[mhd]): (\d+$)',
            string=logtext, flags=MULTILINE)

        found_intvls: list = findall(
            r'^(.*); Tasks reported .+ (\d+[mhd]): (\d+$)',
            string=logtext, flags=MULTILINE)
        found_intvl_avgt: list = findall(
            r'Tasks reported .+\n.+ avg (\d{2}:\d{2}:\d{2})',
            string=logtext, flags=MULTILINE)
        found_intvl_t_range: list = findall(
            r'Tasks reported .+\n.+\n.+ range \[(\d{2}:\d{2}:\d{2}) -- (\d{2}:\d{2}:\d{2})]',
            string=logtext, flags=MULTILINE)

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
            intvl_t_wtmean: str = T.logtimes_stat(distribution=found_intvl_avgt,
                                                  stat='weighted_mean',
                                                  weights=intvl_counts)
            intvl_t_stdev: str = T.logtimes_stat(distribution=found_intvl_avgt,
                                                 stat='stdev',
                                                 weights=intvl_counts)

            # https://www.geeksforgeeks.org/python-convert-list-of-tuples-into-list/
            # Note: using an empty tuple as a sum() starting value flattens the
            #    list of string tuples into one tuple of strings.
            intvl_t_range: str = T.logtimes_stat(distribution=sum(found_intvl_t_range, ()),
                                                 stat='range')

            # Text & data used in most count reporting conditions below:
            if len(set(intvl_vals)) == 1:
                logged_intvl_report = (
                    'Analysis of reported tasks logged from\n'
                    f'{intvl_dates[0]} to {intvl_dates[-1]}\n'
                    f'   {cls.uptime(logtext).ljust(11)} hours counting tasks\n'
                    f'   {str(num_tasks).ljust(11)} tasks in {len(intvl_counts)} count intervals\n'
                    f'   {str(intvl_cnt_avg).ljust(11)} tasks per {intvl_vals[0]} count interval\n'
                    f'   {intvl_t_wtmean.ljust(11)} weighted mean task time\n'
                    f'   {intvl_t_stdev.ljust(11)} std deviation task time\n'
                    f'   {intvl_t_range} range of task times\n\n'
                )
            else:
                logged_intvl_report = (
                    'Analysis of reported tasks logged from\n'
                    f'{intvl_dates[0]} to {intvl_dates[-1]}\n'
                    f'   {cls.uptime(logtext).ljust(11)} hours counting tasks\n'
                    f'   {str(num_tasks).ljust(11)} tasks in {len(intvl_counts)} count intervals\n'
                    f'   {str(intvl_cnt_avg).ljust(11)} tasks per various length count interval\n'
                    f'   {intvl_t_wtmean.ljust(11)} weighted mean task time\n'
                    f'   {intvl_t_stdev.ljust(11)} std deviation task time\n'
                    f'   {intvl_t_range} range of task times\n\n'
                    f'{len(set(intvl_vals))} different interval lengths are logged:\n'
                    f'   {set(intvl_vals)},\n'
                    '   so interpret results with caution.\n')

        else:  # No interval counts found.
            messagebox.showinfo(
                title='No counts available',
                detail='There are no data to analyze.\n'
                       'Need at least one interval count\n'
                       'to analyze results in log file.'
            )

        # Need to check whether plotting is available and possible.
        plot_data = (intvl_dates, found_intvl_avgt, found_intvl_t_range,
                     intvl_counts, intvl_vals)
        cls.check_for_plotting(do_plot=do_plot,
                               intervals=found_intvls,
                               args=plot_data)

        ######## Generate text & data to display in show_analysis(). ##########
        # Need 'recent' vars when there are interval counts following last summary.
        #   So find the list index for first interval count after the last summary.
        #   If there are no intervals after last summary, then flag and move on.
        if found_sumrys and found_intvls:
            try:
                # When there are no intervals after last summary, the last
                #  intvl date is last summary date. Times and formats must match.
                if intvl_dates[-1] == sumry_dates[-1]:
                    recent_intervals = False
                else:
                    index = [i for i, date in enumerate(intvl_dates) if date == sumry_dates[-1]]
                    index_recent = index[0] + 1  # <- The interval after the last summary.
                    recent_dates, recent_intvl_vals, recent_cnts = zip(*found_intvls[index_recent:])
                    num_recent_intvl_vals = len(set(recent_intvl_vals))
                    recent_counts = list(map(int, recent_cnts))
                    num_recent_tasks = sum(recent_counts)
                    recent_t_wtmean = T.logtimes_stat(
                        distribution=found_intvl_avgt[index_recent:],
                        stat='weighted_mean',
                        weights=recent_counts)
            except IndexError:
                summary_text = 'An index error occurred. Cannot analyse log data.\n'
                recent_interval_text = (
                    'Quick fix: backup then delete the log file; restart program.\n'
                    'See menu bar Help > "File paths" for log file location.\n'
                )
                return summary_text, recent_interval_text

        # Need to tailor report texts for various counting conditions.
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
                    f'There are {num_intvl_vals} different interval durations\n'
                    f'logged: {", ".join(set(intvl_vals))},\n'
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
        if found_sumrys and found_intvls and recent_intervals:
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
                    f'There are {num_recent_intvl_vals} different interval lengths,\n'
                    f'   {set(recent_intvl_vals)},\n'
                    '   so interpret results with caution.\n'
                )

        return summary_text, recent_interval_text

    @ classmethod
    def check_log_size(cls) -> None:
        """
        Check size of log file and alert user if it exceeds 20 MB.
        Called from main CountModeler.log_it.log_start at startup.
        """
        log_file = Path(cls.LOGFILE)
        if log_file.stat().st_size > 20_000_000:
            print(f'\nThe log file {log_file} exceeds 20 MB.\n'
                  'Consider backing it up and deleting it before the next program restart.\n'
                  'From the main menu, do: File > Backup log file.\n'
                  'The backup file will be saved in the same directory as the original file\n'
                  '  with a timestamp appended to the filename.\n'
                  'Do not delete the log file while the program is running.\n')

    @classmethod
    def check_for_plotting(cls, do_plot: bool, intervals: list, args: tuple) -> None:
        """
        Check for availability of Matplotlib and data to plot.
        Called from analyze_logfile().
        Calls plot_data() when Matplotlib is available and data is present.

        :param do_plot: When True, call plot_data().
        :param intervals: List of interval counts found in log file.
        :param args: Tuple of interval data lists to plot; a passthrough
                     to plot_data().
        :return: None
        """
        if do_plot and 'matplotlib' in sys.modules:
            if intervals:
                cls.plot_data(*args)
            else:
                messagebox.showinfo(
                    title='No counts available',
                    detail='Need at least one interval count to plot task completion times.'
                )
        elif do_plot:
            messagebox.showinfo(
                title='Plotting not available.',
                detail='Install Matplotlib with: pip install -U matplotlib'
            )

    @classmethod
    def plot_data(cls, intvl_dates: list,
                  found_intvl_avgt: list,
                  found_intvl_t_range: list,
                  intvl_counts: list,
                  intvl_vals: list) -> None:

        """
        Draw plot window of task times and counts (optional) for
        intervals recorded in LOGFILE.
        The plot will be navigable via toolbar buttons on Linux and
        Windows platforms, not on macOS.
        Parameter lists of data distributions need to be same length.
        Called from analyze_logfile() when do_plot=True.

        :param intvl_dates: List of datetime strings for interval counts.
        :param found_intvl_avgt: List of task completion times for intervals.
        :param found_intvl_t_range: List of min and max task times for intervals.
        :param intvl_counts: List of task counts for intervals.
        :param intvl_vals: List of unique time durations of intervals.

        :return: None
        """
        intvl_length: str = ', '.join(set(intvl_vals))

        # Font sizing adapted from Duarte's answer at:
        # https://stackoverflow.com/questions/3899980/
        #   how-to-change-the-font-size-on-a-matplotlib-plot
        if MY_OS == 'lin':
            small_font = 9
            medium_font = 12
            bigger_font = 14
        else:  # macOS (darwin), Windows (win)
            small_font = 7
            medium_font = 10
            bigger_font = 12

        # Initialize fig Figure for Windows, adjust platform-specific sizes:
        fig, ax1 = plt.subplots(figsize=(7.25, 5.75), constrained_layout=True)

        if MY_OS == 'lin':
            fig, ax1 = plt.subplots(figsize=(8, 6), constrained_layout=True)
        elif MY_OS == 'dar':
            fig, ax1 = plt.subplots(figsize=(6.5, 5), constrained_layout=True)

        if cls.DO_TEST:
            ax1.set_title('-- TEST PLOTS of EXAMPLE LOG DATA --',
                          fontsize=bigger_font)
        else:
            ax1.set_title('Task data for logged count intervals',
                          fontsize=bigger_font)
            # fig.suptitle('Task data for logged count intervals',
            #              fontsize=14, fontweight='bold', color=LIGHT_COLOR)

        ax1.set_xlabel('Datetime of interval count\n'
                       '(yr-mo > yr-mo-date > mo-date hr)', fontsize=medium_font)
        ax1.set_ylabel('Task completion time, interval avg.\n'
                       '(hr:min:sec)', fontsize=medium_font)

        ax1.title.set_color(LIGHT_COLOR)
        ax1.yaxis.label.set_color(LIGHT_COLOR)
        ax1.xaxis.label.set_color(LIGHT_COLOR)
        ax1.tick_params(axis='x', which='both', colors=LIGHT_COLOR)
        ax1.tick_params(axis='y', which='both', colors=LIGHT_COLOR)

        # Need to convert intvl_dates and found_intvl_avgt strings to Matplotlib dates;
        #   this greatly speeds up plotting when axes are date objects.
        ax1.xaxis.axis_date()
        ax1.yaxis.axis_date()

        tdates = [mdates.datestr2num(d) for d in intvl_dates]
        ttimes = [mdates.datestr2num(t) for t in found_intvl_avgt]

        mins, maxs = zip(*found_intvl_t_range)
        mintimes = [mdates.datestr2num(m) for m in mins]
        maxtimes = [mdates.datestr2num(m) for m in maxs]

        ax1.scatter(tdates, mintimes, marker='^', s=6,
                    color=MARKER_COLOR3,
                    label='min time')
        ax1.scatter(tdates, maxtimes, marker='v', s=6,
                    color=MARKER_COLOR3,
                    label='max time')
        ax1.scatter(tdates, ttimes, s=4,
                    label='avg. task time')

        ax1.legend(framealpha=0.3,
                   facecolor=LIGHT_COLOR, edgecolor='black',
                   fontsize=small_font,
                   loc='upper left')

        # Need to rotate and right-align the date labels to avoid crowding.
        for label in ax1.get_xticklabels(which='major'):
            label.set(rotation=30, horizontalalignment='right')
        for label in ax1.get_yticklabels(which='major'):
            label.set(rotation=30)

        ax1.yaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        ax1.yaxis.set_minor_locator(tck.AutoMinorLocator())

        ax1.autoscale(True)
        ax1.grid(True)
        fig.set_facecolor(DARK_BG)
        ax1.set_facecolor(LIGHT_COLOR)

        # Show task count's right (second) Y-axis at startup, but hide
        #   its data. Show and hide count data with a toggle command
        #   from a "Show count data" ttk.Button() in the plot window.
        ax2 = ax1.twinx()
        ax2.set_ylabel('Interval task count', color=MARKER_COLOR2)
        ax2.spines['right'].set_color(MARKER_COLOR2)
        ax2.tick_params(axis='y', colors=MARKER_COLOR2)
        ax2.xaxis.axis_date()
        ax2.xaxis.set_minor_locator(mdates.DayLocator())
        ax2.set_zorder(-1)
        # Count markers become 'hidden' because color becomes transparent.
        ax2.scatter(tdates, intvl_counts, alpha=0)

        cls.plot_display(fig=fig, ax2=ax2,
                         tdates=tdates,
                         tcounts=intvl_counts,
                         intvl_length=intvl_length)

    @staticmethod
    def plot_data_toggle(button: tk.Button,
                         figure: plt.Axes,
                         axis: plt.Axes,
                         xdata: list,
                         ydata: list) -> None:
        """
        Show/hide matplotlib data for a 2nd Y axis.
        Toggle is controlled by Button(). *axis* configurations for spine
        tick_params, locators, and label should already be defined.
        Which y-axis coordinates are tracked in the navigation
        toolbar is managed with the zorder() function, as described in:
        https://stackoverflow.com/questions/21583965/
        matplotlib-cursor-value-with-two-axes

        :param button: The calling button to toggle
        :param figure: The matplotlib subplot figure object.
        :param axis: The data axis to toggle, e.g., 2nd y-axis.
        :param xdata: The (shared) x-axis data distribution list.
        :param ydata: The 2nd y-axis data distribution list to toggle,
            e.g. interval task counts.
        :return: None
        """

        if button.cget('text') == 'Show count data':
            button.config(text='Hide count data')

            axis.scatter(xdata, ydata,
                         marker='.', s=6, color=MARKER_COLOR2)
            axis.set_zorder(1)

        else:  # button text is 'Hide count data'
            # Marker "hides" because color becomes transparent.
            button.config(text='Show count data')

            axis.scatter(xdata, ydata,
                         marker='.', alpha=0)
            axis.set_zorder(-1)

        figure.canvas.draw()

    @classmethod
    def plot_display(cls,
                     fig: plt.Axes,
                     ax2: plt.Axes,
                     tdates: list,
                     tcounts: list,
                     intvl_length: str) -> None:
        """
        Show plot Canvas, control, and information widgets in a toplevel
        window.

        :param fig: The matplotlib subplot figure object.
        :param ax2: The 2nd (shared) y-axis; used only as a passthrough
            for call to button's plot_data_toggle().
        :param tdates: The x-axis datetime distribution list.
        :param tcounts: The 2nd y-axis task count distribution list; used
            only as a passthrough for call to plot_data_toggle().
        :param intvl_length: Unique time duration value(s) of intervals.
        :return: None
        """

        # Need a toplevel window for the plot Canvas so that the interval
        #   thread can continue counting; a naked Matplotlab figure
        #   window will run in the same thread as main and pause
        #   the interval timer and counts.
        # Allow resizing of plot canvas with the plot window.
        plotwin = tk.Toplevel()
        plotwin.title('Plots of task data')
        plotwin.minsize(500, 250)
        plotwin.rowconfigure(4, weight=1)
        plotwin.columnconfigure(0, weight=1)
        plotwin.configure(bg=DARK_BG)
        plotwin.protocol('WM_DELETE_WINDOW', lambda: close_plots(plotwin))

        # Put the plot and toolbar drawing areas onto a Canvas, which
        #   will then be put in a Frame().
        canvas = backend.FigureCanvasTkAgg(fig, master=plotwin)
        canvas.get_tk_widget().config(bg=DARK_BG)

        toolbar = backend.NavigationToolbar2Tk(canvas, plotwin)
        # Have toolbar colors match plot and figure colors.
        # Toolbar color: https://stackoverflow.com/questions/48351630/
        toolbar.config(bg=DARK_BG)
        toolbar._message_label.config(bg=DARK_BG, fg=LIGHT_COLOR, padx=40)

        # Need to remove the subplots navigation button.
        # Source: https://stackoverflow.com/questions/59155873/
        #   how-to-remove-toolbar-button-from-navigationtoolbar2tk-figurecanvastkagg
        toolbar.children['!button4'].pack_forget()

        def toggle():
            cls.plot_data_toggle(count_data_btn, fig, ax2, tdates, tcounts)

        # Need a button to toggle display of task count data.
        count_data_btn = ttk.Button(plotwin,
                                    text='Show count data',
                                    command=toggle,
                                    width=0,
                                    style='Plot.TButton'
                                    )

        # Need to set style for count_data_button b/c ttk is the only way
        #   to configure button colors on macOS.
        style = ttk.Style()
        style.configure('Plot.TButton', font=('TkTooltipFont', 9),
                        background=DARK_BG, foreground=MARKER_COLOR2,
                        borderwidth=3
                        )

        # Need to inform user of the number of data points in the plot
        #   and the duration(s) of count intervals.
        num_samples = tk.Label(plotwin,
                               text=f'N = {len(tdates)}',
                               bg=DARK_BG, fg=LIGHT_COLOR
                               )
        interval_duration = tk.Label(plotwin,
                                     text=f'Interval(s): {intvl_length}',
                                     bg=DARK_BG, fg=LIGHT_COLOR
                                     )

        # Now display all widgets:
        toolbar.grid(row=0, column=0, sticky=tk.EW)
        num_samples.grid(row=1, column=0, padx=40, sticky=tk.E)
        interval_duration.grid(row=2, column=0, padx=40, sticky=tk.E)
        count_data_btn.grid(row=3, column=0, padx=40, sticky=tk.E)
        canvas.get_tk_widget().grid(row=4, column=0,
                                    padx=30, pady=(0, 30),
                                    sticky=tk.NSEW
                                    )

    @classmethod
    def show_analysis(cls, tk_obj: tk, do_test=False) -> None:
        """
        Generate a Toplevel window to display cumulative logged task
        data that have been analyzed by cls.analyze_logfile().
        Button appends displayed results to an analysis log file.
        Called from a cls.view() button or a master keybinding.

        :param tk_obj: The tk object over which to display the Toplevel,
            usually a Toplevel window.
        :param do_test: When True, plotting and analysis are tested with
            example log data instead of with working log file data.
        :return: None
        """

        # NOTE: When the log file is not found by analyze_logfile(), the
        #   returned texts will be empty, so no need to continue.
        if do_test:
            summary_text, recent_interval_text = cls.analyze_logfile(do_test=True)
        else:
            summary_text, recent_interval_text = cls.analyze_logfile()
        if not summary_text and not recent_interval_text:
            return

        # Have bg match self.master_bg of the app main window.
        analysiswin = tk.Toplevel(bg='SteelBlue4')
        if cls.DO_TEST:
            analysiswin.title('-- TEST ANALYSIS of EXAMPLE LOG DATA --')
        else:
            analysiswin.title('Analysis of logged data')
        # Need to position window over the window from which it is called.
        analysiswin.geometry(Utils.position_wrt_window(window=tk_obj))
        analysiswin.minsize(width=520, height=320)

        # topmost helps position the window when user calls Help option
        #   to test with example log data.
        analysiswin.attributes('-topmost', True)

        insert_txt = summary_text + recent_interval_text

        max_line = len(max(insert_txt.splitlines(), key=len))

        # Separator dash from https://coolsymbol.com/line-symbols.html.
        # print(ord("─")) -> 9472
        #   unicodedata.name(chr(9472)) -> 'BOX DRAWINGS LIGHT HORIZONTAL'.
        # print(ord("═")) -> 9552
        #   unicodedata.name(chr(9552)) -> 'BOX DRAWINGS DOUBLE HORIZONTAL'.
        sep = f'\n{"─" * max_line}\n'
        insert_txt += sep
        num_lines = insert_txt.count('\n')

        analysistxt = tk.Text(analysiswin, font='TkFixedFont',
                              width=max_line, height=num_lines,
                              bg='grey100', fg='grey5',
                              relief='groove', bd=4,
                              padx=15, pady=10
                              )
        analysistxt.insert(1.0, insert_txt)
        analysistxt.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

        # Need to allow user to save annotated analysis text.
        def new_text():
            new_txt = analysistxt.get(1.0, tk.END)
            Files.append_txt(dest=cls.ANALYSISFILE,
                             savetxt=new_txt,
                             showmsg=True,
                             parent=analysiswin)

        ttk.Button(analysiswin, text='Save analysis', command=new_text,
                   takefocus=False).pack(padx=4)

        Binds.click('right', analysistxt)
        Binds.keybind('close', analysiswin)
        Binds.keybind('append', analysiswin, cls.ANALYSISFILE, insert_txt)
        analysiswin.bind('<Shift-Control-A>',
                         lambda _: cls.view(cls.ANALYSISFILE, tk_obj))

    @staticmethod
    def uptime(logtext: str) -> str:
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
        start_dt = T.str2dt('1970-Jan-01 00:00:00', LONG_STRFTIME)

        # Need to calc uptime hours for all start-to-finish segments that
        #   have interval task counts.
        # Datetimes that begin each log entry are formatted as,
        #    '2021-Dec-05 16:33:49; ...'; LONG_FMT is the time
        #     format used in the log file.
        for line in logtext.split('\n'):
            if 'most recent BOINC report' in line:
                starttime_match = search(
                    r'^(.+); .+ most recent BOINC report', line).group(1)
                start_dt = T.str2dt(starttime_match, LONG_STRFTIME)
            if 'Tasks reported' in line:
                intvltime_match = search(
                    r'^(.+); Tasks reported', line).group(1)
                interval_dt = T.str2dt(intvltime_match, LONG_STRFTIME)
                start2intvls.append(T.duration('hours', start_dt, interval_dt))
                if any(hr < 0 for hr in start2intvls):
                    return 'cannot determine'

        # To calculate total interval hours, need a list of local maximums
        #    from all logged start-to-finish segments of count intervals.
        # There is no need for condition of no logged interval hours b/c
        #    this is only called from analyze_logfile() when there are hrs.
        for i, _hr in enumerate(start2intvls):
            if len(start2intvls) == 1 or i == len(start2intvls) - 1 or start2intvls[i + 1] < _hr:
                intvl_duration.append(_hr)

        return str(round(sum(intvl_duration), 1))

    @classmethod
    def view(cls,
             filepath: Path,
             tk_obj: tk) -> None:
        """
        Create a separate Toplevel window to view a text file as
        scrolled text.

        :param filepath: A Path object of the file to view.
        :param tk_obj: The tk object over which to display the Toplevel,
            usually a window object.
        """
        # Need to set messages and sizes specific to OS and files.
        text_height = 30
        minsize_w = 0
        minsize_h = 0
        fnf_query = ''

        # Need to set platform-specific window width so to not hide Buttons.
        # Widths depend on each platform's TkFixedFont width in filetext.
        if filepath == cls.LOGFILE:
            minsize_h = 220
            if MY_OS == 'lin':
                minsize_w = 800
            if MY_OS == 'win':
                minsize_w = 840
            if MY_OS == 'dar':
                minsize_w = 675
            fnf_query = 'Was the log option ticked in settings?'

        elif filepath == cls.ANALYSISFILE:
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

        insert_txt = Path(filepath).read_text(encoding='utf-8')

        # Use a "dark" background/foreground theme for file text.
        filetext = ScrolledText(filewin, font='TkFixedFont',
                                height=text_height,
                                bg='grey20', fg='grey80',
                                insertbackground='grey80',
                                relief='groove', bd=4,
                                padx=12
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

        # NOTE: To call filepaths() in the main script, *tk_obj* must be
        #   passed as 'app', which is the main (root) object,
        #   CountController(), in the main script. This seems awkward.
        # if str(tk_obj) == '.':  # <- the root (app) window's path name.
        if tk_obj.winfo_parent() == '':
            ttk.Button(
                filewin, text='File path',
                command=lambda: tk_obj.filepaths(filewin),
                takefocus=False).pack(padx=4)

        if filepath == cls.LOGFILE:
            ttk.Button(filewin, text='Analysis',
                       command=lambda: cls.show_analysis(filewin),
                       takefocus=False).pack(padx=4)
            ttk.Button(filewin, text='Plot times',
                       command=lambda: cls.analyze_logfile(do_plot=True),
                       takefocus=False).pack(padx=4)
            filewin.bind('<Shift-Control-L>',
                         lambda _: cls.show_analysis(filewin))
            filewin.bind('<Shift-Control-A>',
                         lambda _: cls.view(cls.ANALYSISFILE, tk_obj))
            # filewin.bind('<Shift-Control-P>',
            #              lambda _: cls.analyze_logfile(plot=True))

        elif filepath == cls.ANALYSISFILE:
            filewin.geometry(Utils.position_wrt_window(window=tk_obj))
            ttk.Button(
                filewin, text='Erase',
                command=lambda: Files.erase(filetext, cls.ANALYSISFILE, filewin),
                takefocus=False).pack(padx=4)
            filewin.bind('<Shift-Control-L>',
                         lambda _: cls.show_analysis(tk_obj))

        Binds.click('right', filewin)
        Binds.keybind('close', filewin)
        Binds.keybind('saveas', filewin, None, filepath)
