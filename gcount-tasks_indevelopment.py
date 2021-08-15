# !/usr/bin/env python3

"""
A tkinter-based GUI version of count-tasks.py using a MVC architecture.
Alpha ver: interval counts not active.

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
# ^^ Info for --about invocation argument >>
__author__ = 'cecht, BOINC ID: 990821'
__copyright__ = 'Copyright (C) 2020 C. Echt'
__credits__ = ['Inspired by rickslab-gpu-utils',
               'Keith Myers - Testing, debug']
__license__ = 'GNU General Public License'
__version__ = '0.1x'
__program_name__ = 'count-tasks.py'
__maintainer__ = 'cecht'
__docformat__ = 'reStructuredText'
__status__ = 'Development Status :: 5 - ALPHA'

import logging
import random
import shutil
import statistics as stats
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from COUNTmodules import boinc_command

try:
    import tkinter as tk
    import tkinter.ttk as ttk
    # pylint: disable=unused-import
    import tkinter.font
    from tkinter import messagebox
    from tkinter.scrolledtext import ScrolledText
except (ImportError, ModuleNotFoundError) as error:
    print('gcount_tasks.py requires tkinter, which is included with some Python 3.7+'
          '\ndistributions, such as from Active State.'
          '\nInstall 3.7+ or re-install Python and include Tk/Tcl.'
          '\nDownloads available from python.org'
          '\nOn Linux-Ubuntu you may need: sudo apt install python3-tk'
          f'\nSee also: https://tkdocs.com/tutorial/install.html \n{error}')

if sys.version_info < (3, 6):
    print('Program requires at least Python 3.6.')
    sys.exit(1)

MY_OS = sys.platform[:3]
# MY_OS = 'win'  # TESTING
TIME_FORMAT = '%Y-%b-%d %H:%M:%S'
BC = boinc_command.BoincCommand()
# # Assume log file is in the CountBOINCtasks-master folder.
# # Not sure what determines the relative Project path.
# #    Depends on copying the module?
# LOGPATH = Path('../count-tasks_log.txt')
LOGPATH = Path('count-tasks_log.txt')
BKUPFILE = 'count-tasks_log(copy).txt'
PROGRAM_VER = '0.5x'
# GUI_TITLE = __file__
GUI_TITLE = 'BOINC task counter'

# Here logging is lazily employed to manage the file of report data.
logging.basicConfig(filename=str(LOGPATH), level=logging.INFO, filemode="a",
                    format='%(message)s')


# Functions used by count-tasks, but not part of MVC structure %%%%%%%%%%%%%%%%%
# pylint: disable=unused-argument
def quit_gui(event=None) -> None:
    """Safe and informative exit from the program.

    :param event: Needed for keybindings.
    :type event: Direct call from keybindings.
    """
    print('\n  *** User has quit the program. ***\n Exiting...\n')
    app.destroy()
    sys.exit(0)

# END Functions used by count-tasks, but not part of MVC structure %%%%%%%%%%%%%


# The tkinter gui engine that runs as main thread.
class CountViewer(tk.Frame):
    """
    The Viewer communicates with Modeler via 'share' objects handled
    through the Controller class. All GUI widgets go here.
    """
    
    def __init__(self, master, share):
        super().__init__(master)
        self.share = share
        self.time_start = datetime.now().strftime(TIME_FORMAT)

        # Set colors for row labels and data display
        # http://www.science.smith.edu/dftwiki/index.php/Color_Charts_for_TKinter
        self.row_fg = 'LightCyan2'  # foreground for row labels
        self.data_bg = 'grey40'  # background for data labels and frame
        self.master_bg = 'SkyBlue4'  # also used for row header labels.

        self.dataframe = tk.Frame()
        
        # Label foreground configuration variables
        self.emphasize = 'grey90'
        self.highlight = 'gold'
        self.deemphasize = 'grey60'
        
        # Log print formatting:
        self.report = 'none'
        self.indent = ' ' * 22
        self.bigindent = ' ' * 33

        # self.settings() & self.check_and_set var:
        self.close_settings = 'None'
        
        # Basic run parameters/settings; passed between Viewer and Modeler.
        # Defaults set in Modeler.default_settings; changed in settings(),
        #   except time_start.
        self.share.setting = {
            'time_start': tk.StringVar(),
            'interval_t': tk.StringVar(),
            'sumry_t_val': tk.IntVar(),
            'sumry_t_unit': tk.StringVar(),
            'summary_t': tk.StringVar(),
            # NOTE: cycles_max works fine as an IntVar; testing using as StringVar
            'cycles_max': tk.StringVar(),
            'do_log': tk.IntVar()
        }
        
        # Common data var for reporting; passed between Viewer and Modeler
        self.share.tkdata = {
            # Common data reports var
            'tt_mean': tk.StringVar(),
            'tt_sd': tk.StringVar(),
            'tt_min': tk.StringVar(),
            'tt_max': tk.StringVar(),
            'tt_range': tk.StringVar(),
            'tt_total': tk.StringVar(),
            'time_now': tk.StringVar(),
            'counts_remain': tk.IntVar(),
            'count_next': tk.StringVar(value="countdown clock goes here"),
            # Unique to interval data report var
            'count_new': tk.IntVar(),
            'tic_nnt': tk.IntVar(),
            # Unique to summary data report var
            'count_uniq': tk.IntVar(),
            'num_tasks': tk.IntVar()
        }
    
        # TODO: Figure out why ttk.Style wasn't working; changed all to tk.Label()
        # style_data = ttk.Style(self.dataframe)
        # style_data.configure('TLabel', foreground=self.row_fg,
        #                       background=self.data_bg, anchor='center')

        # Labels for run settings, configure in show_startdata():
        self.time_start_l = tk.Label(self.dataframe, bg=self.data_bg,
                                     fg='grey90')
        self.interval_t_l = tk.Label(self.dataframe, width=20,
                                     textvariable=self.share.setting['interval_t'], # GO, but no unit
                                     relief='groove', borderwidth=2, bg=self.data_bg)
        self.summary_t_l = tk.Label(self.dataframe, width=20,
                                    textvariable=self.share.setting['summary_t'],
                                    relief='groove', borderwidth=2, bg=self.data_bg)
        self.cycles_max_l = tk.Label(textvariable=self.share.setting['cycles_max'],
                                     background=self.master_bg, foreground=self.row_fg)

        # Labels for BOINC data; gridded in their respective show_methods().
        self.count_start_l = tk.Label(self.dataframe, width=3, bg=self.data_bg)
        self.count_new_l = tk.Label(self.dataframe, width=3, bg=self.data_bg,
                                    textvariable=self.share.tkdata['count_new'])
        self.count_uniq_l = tk.Label(self.dataframe, width=3, bg=self.data_bg,
                                     textvariable=self.share.tkdata['count_uniq'])
        self.tt_mean_l = tk.Label(self.dataframe, width=3, bg=self.data_bg,
                                  textvariable=self.share.tkdata['tt_mean'])
        self.tt_sd_l = tk.Label(self.dataframe, width=3, bg=self.data_bg,
                                textvariable=self.share.tkdata['tt_sd'])
        self.tt_range_l = tk.Label(self.dataframe, width=3, bg=self.data_bg,
                                   textvariable=self.share.tkdata['tt_range'])
        self.tt_total_l = tk.Label(self.dataframe, width=3, bg=self.data_bg,
                                   textvariable=self.share.tkdata['tt_total'])
        self.ttmean_sumry_l = tk.Label(self.dataframe, width=3, bg=self.data_bg,
                                       textvariable=self.share.tkdata['tt_mean'])
        self.ttsd_sumry_l = tk.Label(self.dataframe, width=3, bg=self.data_bg,
                                     textvariable=self.share.tkdata['tt_sd'])
        self.ttrange_sumry_l = tk.Label(self.dataframe, width=3, bg=self.data_bg)
        self.ttsum_sumry_l = tk.Label(self.dataframe, width=3, bg=self.data_bg,
                                      textvariable=self.share.tkdata['tt_total'])
        
        self.time_now_l = tk.Label(textvariable=self.share.tkdata['time_now'],
                                   background=self.master_bg, foreground=self.row_fg)
        self.count_next_l = tk.Label(textvariable=self.share.tkdata['count_next'],
                                     background=self.master_bg, foreground=self.row_fg)
        self.counts_remain_l = tk.Label(textvariable=self.share.tkdata['counts_remain'],
                                        background=self.master_bg, foreground=self.row_fg)
        self.num_tasks_l = tk.Label(textvariable=self.share.tkdata['num_tasks'],
                                    background=self.master_bg, foreground=self.row_fg)
        # Text for compliment is configured in compliment_me()
        self.share.compliment_txt = tk.Label(fg='orange', bg=self.master_bg,
                                             relief='flat', border=0)
        
        self.config_master()
        self.master_widgets()
        # Need to set window position here (not in config_master),so it doesn't
        #    shift when PassModeler.config_results() is called b/c different
        #    from app position.
        # self.master.geometry('+96+134')  # or app.geometry('+96+134')

    def config_master(self) -> None:
        """
        Set up master window configuration, keybindings, frames, & menus
        """
        # Background color of container Frame is configured in __init__
        # OS-specific window size ranges set in Controller __init__
        # self.master.minsize(466, 365)
        self.master.title(GUI_TITLE)
        # Need to color in all of master Frame, and use light grey border.
        self.master.configure(bg=self.master_bg,
                              highlightthickness=3,
                              highlightcolor='grey75',
                              highlightbackground='grey95')

        # Theme controls entire window theme, but only for ttk.Style objects.
        # Options: classic, alt, clam, default, aqua(MacOS only)
        ttk.Style().theme_use('alt')
        
        # Set up universal and OS-specific keybindings and menus
        self.master.bind_all('<Escape>', quit_gui)
        cmdkey = ''
        if MY_OS in 'lin, win':
            cmdkey = 'Control'
        elif MY_OS == 'dar':
            cmdkey = 'Command'
        self.master.bind(f'<{f"{cmdkey}"}-q>', quit_gui)
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
                      'Last count was:': 10,
                      '# counts to go:': 11,
                      'Next count in:': 12,
                      'Total # tasks:': 13
                      }
        for header, rownum in row_header.items():
            tk.Label(self.master, text=f'{header}',
                     bg=self.master_bg, fg=self.row_fg
                     ).grid(row=rownum, column=0, padx=(5, 0), sticky=tk.E)
    
    def master_widgets(self) -> None:
        """
        Layout menus, buttons, separators, row labels in main window.
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
        file.add_command(label='Settings...', command=self.settings)
        file.add_separator()
        file.add_command(label='Quit', command=quit_gui,
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
        menu.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Compliment", command=self.share.complimentme,
                              accelerator="Ctrl+Shift+C")
        help_menu.add_command(label="About", command=self.share.about)
        
        # Create button widgets:
        style_button = ttk.Style(self.master)
        style_button.configure('TButton', background='grey80', anchor='center')
        
        viewlog_b = ttk.Button(text='View log file', command=self.show_log)
        intvl_b = ttk.Button(text='Interval data', command=self.show_intervaldata)
        self.sumry_b = ttk.Button(text='Summary data', command=self.show_sumrydata)
        quit_b = ttk.Button(text='Quit', command=quit_gui)

        # For colored separators, use ttk.Frame instead of ttk.Separator.
        # Initialize then configure style for separator color.
        style_sep = ttk.Style(self.master)
        style_sep.configure('TFrame', background=self.master_bg)
        sep1 = ttk.Frame(relief="raised", height=6)
        sep2 = ttk.Frame(relief="raised", height=6)
        
        # %%%%%%%%%%%%%%%%%%% grid: sorted by row number %%%%%%%%%%%%%%%%%%%%%%
        viewlog_b.grid(row=0, column=0, padx=5, pady=5)
        intvl_b.grid(row=0, column=1, padx=0, pady=5)
        self.sumry_b.grid(row=0, column=2, padx=(0, 25), pady=5)
        sep1.grid(row=1, column=0, columnspan=5, padx=5, pady=(2, 5), sticky=tk.EW)
        # Intervening rows are gridded in show_startdata()
        sep2.grid(row=9, column=0, columnspan=5, padx=5, pady=(6, 6), sticky=tk.EW)
        # self.start_b.grid(row=13, column=2, padx=(0, 5), sticky=tk.E)
        quit_b.grid(row=13, column=2, padx=(0, 5), pady=(4, 0), sticky=tk.E)
        self.share.compliment_txt.grid(row=14, column=1, columnspan=3,
                                       padx=(30, 0), pady=5, sticky=tk.W)

        self.show_startdata()

    # The show_ methods: define and display data for master window and logging.
    def show_startdata(self) -> None:
        """
        Populate starting count-tasks data labels in master window.
        Log data to file if optioned. Shows default settings and task
        metrics for the most recent BOINC report. Called from Button().
        """
        # Need to define starting settings and BOINC data, via Controller.
        self.share.defaultsettings()
        self.share.getstartdata()

        # Need to keep sumry_b disabled until after 1st summary interval.
        self.sumry_b.config(state=tk.DISABLED)

        # Need self.share... b/c ttimes_start is used in get_interval_data()
        self.share.ttimes_start = BC.get_reported('elapsed time')
        self.count_start = len(self.share.ttimes_start)
        self.time_start_l.config(text=self.time_start)
        self.interval_t_l.config(foreground=self.emphasize)
        self.summary_t_l.config(foreground=self.deemphasize)
        self.count_start_l.config(text=self.count_start,
                                  foreground=self.highlight)
        # count_next Label is config __init__ and set in intvl_timer().
        # num_tasks Label is config __init__ and set in get_start_data().

        # Starting count data and times (from past boinc-client hour).
        # Textvariables are configured in __init__; their values
        #   (along with self.share.tt_range) are set in get_start_data()
        #    and called via Controller getstartdata().
        self.tt_mean_l.configure(foreground=self.highlight)
        self.tt_sd_l.configure(foreground=self.emphasize)
        self.tt_range_l.configure(foreground=self.emphasize)
        self.tt_total_l.configure(foreground=self.emphasize)

        # This start_info label is a one-off; in same grid position as time_now_l.
        start_info_l = ttk.Label(self.master,
                                 text='The most recent 1 hr BOINC report',
                                 background=self.master_bg,
                                 foreground=self.row_fg)

        # Grid the labels; sorted by row.
        # TODO: grid is used here and other show_() to set new label values
        #  with a window redraw. Is that needed when textvariables and share.var are used?
        self.time_start_l.grid(row=2, column=1, padx=(10, 16), sticky=tk.EW,
                               columnspan=2)
        self.interval_t_l.grid(row=3, column=1, padx=(12, 6), sticky=tk.EW)
        self.summary_t_l.grid(row=3, column=2, padx=(0, 16), sticky=tk.EW)
        self.count_start_l.grid(row=4, column=1, padx=10, sticky=tk.EW)
        self.tt_mean_l.grid(row=5, column=1, padx=10, sticky=tk.EW)
        self.tt_sd_l.grid(row=6, column=1, padx=10, sticky=tk.EW)
        self.tt_range_l.grid(row=7, column=1, padx=10, sticky=tk.EW)
        self.tt_total_l.grid(row=8, column=1, padx=10, sticky=tk.EW)
        start_info_l.grid(row=10, column=1, padx=3, sticky=tk.W,
                          columnspan=2)
        self.cycles_max_l.grid(row=11, column=1, padx=3, sticky=tk.W)
        self.count_next_l.grid(row=12, column=1, padx=3, sticky=tk.W)
        self.num_tasks_l.grid(row=13, column=1, padx=3, sticky=tk.W)

        if self.share.setting['do_log'].get() == 1:
            interval_t = self.share.setting['interval_t'].get()
            summary_t = self.share.setting['summary_t'].get()
            tt_mean = self.share.tkdata['tt_mean'].get()
            tt_sd = self.share.tkdata['tt_sd'].get()
            tt_range = self.share.tkdata['tt_range'].get()
            tt_total = self.share.tkdata['tt_total'].get()
            num_tasks = self.share.tkdata['num_tasks'].get()
            cycles_max = self.share.setting['cycles_max'].get()
            if int(cycles_max) > 0:
                self.report = (
                    ">>> TASK COUNTER START settings <<<\n"
                    f'{self.time_start}; Number of tasks in the most recent BOINC report:'
                    f' {self.count_start}\n'
                    f'{self.indent}Task Time: mean {tt_mean},'
                    f' range [{tt_range}],\n'
                    f'{self.bigindent}stdev {tt_sd}, total {tt_total}\n'
                    f'{self.indent}Total tasks in queue: {num_tasks}\n'
                    f'{self.indent}Number of scheduled count intervals: {cycles_max}\n'
                    f'{self.indent}Counts every {interval_t},'
                    f' summaries every {summary_t}\n'
                    f'Timed intervals beginning now...\n\n')
            # Need to provide a truncated report for one-off "status" runs.
            elif int(cycles_max) == 0:
                self.report = (
                    f'{self.time_start}; Number of tasks in the most recent BOINC report:'
                    f' {self.count_start}\n'
                    f'{self.indent}Task Time: mean {self.share.tt_mean},'
                    f' range [{range}],\n'
                    f'{self.bigindent}stdev {self.share.tt_sd}, total {self.share.tt_total}\n'
                    f'{self.indent}Total tasks in queue: {num_tasks}\n')
        logging.info(self.report)

        # self.show_intervaldata()
        
    # TODO: Consider whether need to re-grid labels for intervals. Just use
    #  configure and master.update() ?  Is StringVar enough to update data?
    def show_intervaldata(self) -> None:
        """
        Show interval and summary metrics for most recently read BOINC
        task data.
        """
        
        self.interval_t_l.config(foreground=self.emphasize)
        self.summary_t_l.config(foreground=self.deemphasize)
        
        # Interval data, column1
        self.count_new_l.configure(foreground=self.highlight)
        self.tt_mean_l.configure(foreground=self.highlight)
        self.tt_sd_l.configure(foreground=self.emphasize)
        self.tt_range_l.configure(foreground=self.emphasize)
        self.tt_total_l.configure(foreground=self.emphasize)
        
        # Summary data, column2, deemphasize font color
        self.count_uniq_l.configure(foreground=self.deemphasize)
        self.ttmean_sumry_l.configure(foreground=self.deemphasize)
        self.ttsd_sumry_l.configure(foreground=self.deemphasize)
        self.ttrange_sumry_l.configure(foreground=self.deemphasize)
        self.ttsum_sumry_l.configure(foreground=self.deemphasize)
        
        # Previous and until task count times.
        self.count_new_l.configure(text=self.count_new)
        self.time_now_l.configure(text=self.time_now)
        self.count_next_l.configure(text=self.share.tkdata['count_next'].get())
        
        # Place new labels (not in show_startdata) in row,column positions.
        # Also place labels whose font emphasis needs to change. ???
        self.count_new_l.grid(row=4, column=1, padx=10, sticky=tk.EW)
        self.time_now_l.grid(row=10, column=1, padx=3, sticky=tk.W,
                             columnspan=2)
        self.counts_remain_l.grid(row=11, column=1, padx=3, sticky=tk.W)
        self.count_next_l.grid(row=12, column=1, padx=3, sticky=tk.W)
        self.num_tasks_l.grid(row=13, column=1, padx=3, sticky=tk.W)

        # self.master.update()
        # self.master.update_idletasks()

    def show_sumrydata(self) -> None:
        """
        Show and emphasize summary count-tasks data in GUI window.

        :return: Multi-interval averaged task data.
        """
        self.sumry_b.config(state=tk.NORMAL)

        # Count and summary interval times
        tt_range = f'{self.tt_min.get()} -- {self.tt_max.get()}'
        
        self.interval_t_l.config(foreground=self.deemphasize)
        self.summary_t_l.config(foreground=self.emphasize)
        
        # Summary data, column2, emphasize font color
        self.count_uniq_l.configure(foreground=self.highlight)
        self.ttmean_sumry_l.configure(foreground=self.highlight)
        self.ttsd_sumry_l.configure(foreground=self.emphasize)
        self.ttrange_sumry_l.configure(text=tt_range,
                                       foreground=self.emphasize)
        self.ttsum_sumry_l.configure(foreground=self.emphasize)
        
        # Interval data, column1, deemphasize font color
        self.count_start_l.configure(foreground=self.deemphasize)
        self.count_new_l.configure(foreground=self.deemphasize)
        self.tt_mean_l.configure(foreground=self.deemphasize)
        self.tt_sd_l.configure(foreground=self.deemphasize)
        self.tt_range_l.configure(foreground=self.deemphasize)
        self.tt_total_l.configure(foreground=self.deemphasize)
    
        
        # Place labels in row,column positions.
        # Need to match padx spacing among all column 2 labels elsewhere.
        self.count_uniq_l.grid(row=4, column=2, padx=(0, 16), sticky=tk.EW)
        self.ttmean_sumry_l.grid(row=5, column=2, padx=(0, 16), sticky=tk.EW)
        self.ttsd_sumry_l.grid(row=6, column=2, padx=(0, 16), sticky=tk.EW)
        self.ttrange_sumry_l.grid(row=7, column=2, padx=(0, 16), sticky=tk.EW)
        self.ttsum_sumry_l.grid(row=8, column=2, padx=(0, 16), sticky=tk.EW)
        
        self.time_now_l.grid(row=10, column=1, padx=3, sticky=tk.W,
                             columnspan=2)
        self.counts_remain_l.grid(row=11, column=1, padx=3, sticky=tk.W)
        self.count_next_l.grid(row=12, column=1, padx=3, sticky=tk.W)
        self.num_tasks_l.grid(row=13, column=1, padx=3, sticky=tk.W)
        
        # self.master.update_idletasks()
        # master.mainloop()
    
    # Methods for menu items and keybinds.
    @staticmethod
    def show_log() -> None:
        """
        Create a separate window to view the log file.

        :return: Read-only log file as scrolled text.
        """
        
        try:
            with open(LOGPATH, 'r') as log:
                logwin = tk.Toplevel()
                logwin.minsize(665, 520)
                # logwin.attributes('-topmost', 1)  # for Windows, needed?
                logwin.title('count-tasks_log.txt')
                logtext = ScrolledText(logwin, width=79, height=30,
                                       bg='grey85', relief='raised', padx=5)
                logtext.insert(tk.INSERT, log.read())
                logtext.see('end')
                logtext.grid(row=0, column=0, sticky=tk.NSEW)
                logtext.focus_set()
        # TODO: replace print with messagebox
        except FileNotFoundError as fnf_err:
            headsup = ('The file count-tasks_log.txt is not in the'
                       ' CountBOINCtasks-master folder.\n'
                       'Has the file been created with the --log command line'
                       ' option?')
            print(f'{headsup}\n{fnf_err}')
            logwin = tk.Toplevel()
            logwin.attributes('-topmost', 1)  # for Windows, needed?
            logwin.title('View log error')
            logtext = tk.Text(logwin, width=75, height=4, bg='grey85',
                              fg='red', relief='raised', padx=5)
            logtext.insert(tk.INSERT, headsup)
            logtext.grid(row=0, column=0, sticky=tk.NSEW)
            logtext.focus_set()
    
    @staticmethod
    def backup_log() -> None:
        """
        Copy the log file to the home folder; called from File menu.

        :return: A new or overwritten backup file.
        """
        
        destination = Path.home() / BKUPFILE
        if Path.is_file(LOGPATH) is True:
            shutil.copyfile(LOGPATH, destination)
            success_msg = 'Log file has been copied to: '
            success_detail = str(destination)
            # print(success_msg)
            messagebox.showinfo(title='Archive notice',
                                message=success_msg, detail=success_detail)
        else:
            warn_main = f'The file {LOGPATH} cannot be archived'
            warn_detail = ('It is not in the CountBOINCtasks-master '
                           'folder. Has the file been created with the '
                           '--log command line option?\n'
                           'Perhaps it has been moved?')
            # print('\n', warn_main, warn_detail)
            messagebox.showwarning(title='Archive warning',
                                   message=warn_main, detail=warn_detail)
    
    def settings(self) -> None:
        """
        Toplevel window called from menu File>Settings.
        Use to change default parameters for interval times,
        counting limit, log file option; on-the-fly changes.
        """

        # Toplevel window basics
        # Need self. b/c window parent is used for a messagebox in check_and_set().
        self.settings_win = tk.Toplevel(relief='raised', bd=3)
        self.settings_win.title('Set run parameters')
        self.settings_win.attributes('-topmost', True)
        self.settings_win.resizable(False, False)
        x = app.winfo_x()
        y = app.winfo_y()
        self.settings_win.geometry(f'+{x + 500}+{y + 0}')

        # Colors should match those of master/parent window.
        settings_fg = 'LightCyan2'
        settings_bg = 'SkyBlue4'
        self.settings_win.configure(bg=settings_bg)
        style = ttk.Style()
        style.configure('TLabel', background=settings_bg, foreground=settings_fg)

        # Need to disable default window Exit; only allow exit from active Confirm button.
        # https://stackoverflow.com/questions/22738412/a-suitable-do-nothing-lambda-expression-in-python
        #    to just disable 'X' exit, the protocol func can be lambda: None, or type(None)()
        def on_exit():
            msg = ('Please exit window with "Return" button.\n'
                   '"Return" is allowed once "Confirm" button is clicked.')
            messagebox.showinfo(title='Confirm before closing', detail=msg,
                                parent=self.settings_win)
        self.settings_win.protocol('WM_DELETE_WINDOW', on_exit)

        # Functions for Combobox selections.
        def set_intvl_selection(*args):
            self.share.setting['interval_t'].set(self.intvl_choice.get())

        def set_sumry_unit(*args):
            self.share.setting['sumry_t_unit'].set(self.sumry_t_unit.get())

        # Need to restrict entries to only digits,
        #   MUST use action type parameter to allow user to delete first number they enter.
        def test_dig_entry(entry_string, action_type):
            """
            Only digits are accepted and displayed in Entry field.
            Used with .register() to configure Entry validatecommand.
            """
        # source: https://stackoverflow.com/questions/4140437/interactively-validating-entry-widget-content-in-tkinter
            if action_type == '1':  # action type is "insert"
                if not entry_string.isdigit():
                    return False
            return True

        # Have user select interval times for counting and summary cycles.
        self.intvl_choice = ttk.Combobox(self.settings_win, state='readonly', width=4,
                                         textvariable=self.share.setting['interval_t'])
                                    
        self.intvl_choice['values'] = ('60m', '55m', '50m', '45m', '40m', '35m',
                                       '30m', '25m', '20m', '15m', '10m', '5m')
        self.intvl_choice.bind("<<ComboboxSelected>>", set_intvl_selection)

        intvl_label1 = ttk.Label(self.settings_win, text='Count interval')
        intvl_label2 = ttk.Label(self.settings_win, text='minutes')

        self.sumry_t_value = ttk.Entry(self.settings_win,
                                       textvariable=self.share.setting['sumry_t_val'],
                                       validate='key', width=4)
        self.sumry_t_value.configure(validatecommand=(
            self.sumry_t_value.register(test_dig_entry), '%P', '%d'))

        self.sumry_t_unit = ttk.Combobox(self.settings_win, state='readonly',
                                         textvariable=self.share.setting['sumry_t_unit'],
                                         values=('day', 'hr', 'min'), width=4)
        self.sumry_t_unit.bind("<<ComboboxSelected>>", set_sumry_unit)

        sumry_label1 = ttk.Label(self.settings_win, text='Summary interval: time value')
        sumry_label2 = ttk.Label(self.settings_win, text='time unit')

        # Specify number limit of counting cycles to run before program exits.
        self.cycles_max_entry = ttk.Entry(self.settings_win,
                                          textvariable=self.share.setting['cycles_max'],
                                          validate='key', width=4)
        self.cycles_max_entry.configure(
            validatecommand=(self.cycles_max_entry.register(test_dig_entry), '%P', '%d'))

        cycles_label1 = ttk.Label(self.settings_win, text='# Count cycles')
        cycles_label2 = ttk.Label(self.settings_win, text='default 1008')

        # Need a user option to log results to file.
        # 'do_log' value is BooleanVar() & kw variable automatically sets it.
        self.log_choice = tk.Checkbutton(self.settings_win,
                                         variable=self.share.setting['do_log'],
                                         bg=settings_bg, borderwidth=0)
        log_label = ttk.Label(self.settings_win, text='Log results to file')

        confirm_button = ttk.Button(self.settings_win, text='Confirm',
                                    command=self.check_and_set)

        # Default button should display all default values in real time.
        default_button = ttk.Button(self.settings_win, text='Use defaults',
                                    command=self.share.defaultsettings)
        
        self.return_button = ttk.Button(self.settings_win, text='Return',
                                        command=self.settings_win.destroy)
        # Need to disable button to force user to first "Confirm" settings,
        #    even when settings have not been changed: a 2-click close.
        self.return_button.state(["disabled"])

        # Grid all window widgets; sorted by row.
        self.intvl_choice.grid(column=1, row=0)
        intvl_label1.grid(column=0, row=0, padx=5, pady=10, sticky=tk.E)
        intvl_label2.grid(column=2, row=0, padx=5, pady=10, sticky=tk.W)
        sumry_label1.grid(column=0, row=1, padx=(10, 5), pady=10, sticky=tk.E)
        self.sumry_t_value.grid(column=1, row=1)
        sumry_label2.grid(column=2, row=1, padx=5, pady=10, sticky=tk.E)
        self.sumry_t_unit.grid(column=3, row=1, padx=5, pady=10, sticky=tk.W)
        cycles_label1.grid(column=0, row=2, padx=5, pady=10, sticky=tk.E)
        self.cycles_max_entry.grid(column=1, row=2)
        cycles_label2.grid(column=2, row=2, padx=5, pady=10, sticky=tk.W)
        log_label.grid(column=0, row=3, padx=5, pady=10, sticky=tk.E)
        self.log_choice.grid(column=1, row=3, padx=0, sticky=tk.W)
        confirm_button.grid(column=3, row=3, padx=10, pady=10, sticky=tk.E)
        default_button.grid(column=0, row=4, padx=10, pady=(0, 5), sticky=tk.W)
        self.return_button.grid(column=3, row=4, padx=10, pady=(0, 5), sticky=tk.E)

    def check_and_set(self, *args, **kwargs):
        """
        Confirm that summary time > interval time, set all settings
        from settings() to their textvariable dict values, and log to
        file if optioned. Called from settings() Confirm button.
        """
        self.share.setting['cycles_max'].set(self.cycles_max_entry.get())
        # Note: self.share.setting['do_log'] is set automatically by Checkbutton.
        # Note: self.share.setting['interval_t'] is set in settings().
        interval_m = int(self.share.setting['interval_t'].get()[:-1])
        # Need to set summary_t here b/c it's from 2 sumry widgets in settings()
        summary_t = self.sumry_t_value.get() + self.sumry_t_unit.get()[:1]
        self.share.setting['summary_t'].set(summary_t)
        summary_m = self.share.getmin(summary_t)
        if interval_m >= summary_m:
            self.return_button.state(["disabled"])
            info = "Summary time must be greater than interval time"
            messagebox.showerror(title='Invalid entry', detail=info,
                                 parent=self.settings_win)
        elif interval_m < summary_m:
            self.return_button.state(["!disabled"])

        if self.share.setting['do_log'].get() == 1 and interval_m < summary_m:
            time_now = datetime.now().strftime(TIME_FORMAT)
            logging.info(
                f"{time_now}  >>> NEW SETTINGS <<<\n"
                f"{self.indent}Interval time: {self.share.setting['interval_t'].get()}\n"
                f"{self.indent}Summary time: {self.share.setting['summary_t'].get()}\n"
                f"{self.indent}Max. counts before auto-exit: {self.share.setting['cycles_max'].get()}\n"
            )


# The engine that gets BOINC data and runs timed reports.
class CountModeler:
    """
    Timed interval counting, analysis, and reporting of BOINC task data.
    """

    def __init__(self, share):
        self.share = share
        
        # self.time_now = None
        # self.counts_remain = None
        self.num_tasks = 0
        self.report = 'None'
        self.ttimes_new = []
        self.ttimes_smry = []
        self.ttimes_uniq = []
        self.ttimes_used = ['']  # Need a null string in list.
        self.count_new = None
        self.tic_nnt = 0
        self.notrunning = False
        
        # Log file print formatting:
        self.indent = ' ' * 22
        self.bigindent = ' ' * 33

        self.get_start_data()
    
    def default_settings(self) -> None:
        """Set or reset default run parameters in setting dictionary.
        """

        self.share.setting['interval_t'].set('60m')
        self.share.setting['sumry_t_val'].set(1)
        self.share.setting['sumry_t_unit'].set('day')
        self.share.setting['summary_t'].set('1d')
        self.share.setting['cycles_max'].set('1008')
        self.share.setting['do_log'].set(1)
        
        # alternative names, for debugging or just in case...
        # self.share.interval_t = '60m'
        # self.share['sumry_t_val'].set(1)
        # self.share['sumry_t_unit'].set('day')
        # self.share.summary_t = '1d'
        # self.share.cycles_max = '1008'
        # self.share.do_log = 1
    
    def get_start_data(self):
        """Gather initial data to track tasks and times.
        """
        # As with task names, task times as sec.microsec are unique.
        #   In future, may want to inspect task names with
        #     task_names = BC.get_reported('tasks').
        ttimes_start = BC.get_reported('elapsed time')
        # Begin list "old" tasks to exclude from new tasks; list is used
        #   in get_interval_data() to track tasks across intervals.
        self.ttimes_used.extend(ttimes_start)

        # count_start used as param in get_timestats() via Controller
        count_start = len(ttimes_start)

        # num_tasks Label config and grid are defined in Viewer __init__:
        #  set value here for use in show_startdata()
        self.share.tkdata['num_tasks'].set(len(BC.get_tasks('name')))

        startdict = self.get_timestats(count_start, ttimes_start)
        # NOTE: these self.share.var are used for reporting as well as
        #   setting dict values
        self.share.tt_mean = startdict['tt_mean']
        self.share.tt_max = startdict['tt_max']
        self.share.tt_min = startdict['tt_min']
        self.share.tt_sd = startdict['tt_sd']
        self.share.tt_total = startdict['tt_total']
        self.share.tt_range = f'{self.share.tt_min} -- {self.share.tt_max}'
        self.share.tkdata['tt_mean'].set(self.share.tt_mean)
        self.share.tkdata['tt_sd'].set(self.share.tt_sd)
        self.share.tkdata['tt_range'].set(self.share.tt_range)
        self.share.tkdata['tt_total'].set(self.share.tt_total)

    # TODO: Make a get_interval_data(), like get_start_data(), to define textvariables
    #   for the Viewer show_intervaldata()
    def get_interval_data(self) -> None:
        """
        Gather recurring interval data of tasks and times. Report on
        BOINC run and task status.
        """
        # Synopsis:
        # Do not include starting tasks in interval or summary counts.
        # Remove previous ("used") tasks from current ("new") task metrics.
        
        for loop_num in range(self.share.setting['cycles_max'].get()):
            # intvl_timer() sleeps the for-loop between counts.
            interval_minutes = int(self.share.setting['interval_t'].get()[:-1])
            self.intvl_timer(interval_minutes)
            # t.sleep(5)  # DEBUG; or use to bypass intvl_timer.

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
                    time_now = datetime.now().strftime(TIME_FORMAT)
                    report = (f'\n{time_now};'
                              f' *** Project update requested for {first_project}. ***\n')
                    print(report)
                    if self.share.setting['do_log'].get() == 1:
                        logging.info(report)
            
            # Need to add all prior tasks to the "used" list. "new" task times
            #  here are carried over from the prior interval,
            #  (which initially is from get_start_data().)
            self.ttimes_used.extend(self.ttimes_new)
            
            ttimes_sent = BC.get_reported('elapsed time')
            
            # Need to re-set prior ttimes_new, then repopulate it with newly
            #   reported tasks.
            self.ttimes_new.clear()
            self.ttimes_new = [task for task in ttimes_sent if task
                               not in self.ttimes_used]
            # Add new tasks to summary list for later analysis.
            # Counting a set() may not be necessary if ttimes_new list works as
            #   intended, but better to err toward thoroughness and clarity.
            self.ttimes_smry.extend(self.ttimes_new)
            self.count_new = len(set(self.ttimes_new))
            # Need to values in self.share.tkdata dict for use in Viewer.
            self.share.tkdata['count_new'].set(self.count_new)
            self.share.tkdata['num_tasks'].set(self.num_tasks)

            intervaldict = self.get_timestats(self.count_new, self.ttimes_new)
            # NOTE: these self.share.var are used for reporting as well as
            #   setting dict values
            # TODO: DO THESE vals need to be .share.?? b/c only textvariables
            #   from share.tkdata dict use these data, right?
            self.share.tt_mean = intervaldict['tt_mean']
            self.share.tt_max = intervaldict['tt_max']
            self.share.tt_min = intervaldict['tt_min']
            self.share.tt_sd = intervaldict['tt_sd']
            self.share.tt_total = intervaldict['tt_total']
            self.share.tt_range = f'{self.share.tt_min} -- {self.share.tt_max}'

            self.share.tkdata['tt_mean'].set(self.share.tt_mean)
            self.share.tkdata['tt_sd'].set(self.share.tt_sd)
            self.share.tkdata['tt_range'].set(self.share.tt_range)
            self.share.tkdata['tt_total'].set(self.share.tt_total)
            
            # TODO: Add this to show_intervaldata() for Viewer and logging option,
            #  as in show_startdata() (using data set in get_interval_data()
            # Report: Regular intervals
            # Suppress full report for no new tasks, which are expected for
            #   long-running tasks (60 m is longest allowed count interval).
            # Overwrite successive NNT reports for a tidy terminal window;
            #   move cursor up two lines before overwriting: \x1b[2A.
            # Need a notification when tasks first run out.
            # Var used only for logging:
            interval_t = self.share.settings['interval_t']
            time_now = datetime.now().strftime(TIME_FORMAT)
            cycles_max = self.share.setting['cycles_max']
            counts_remain = int(cycles_max) - (loop_num + 1)
            if self.count_new == 0:
                self.tic_nnt += 1
                report = (f'{time_now}; '
                          'NO TASKS reported in the past'
                          f' {self.tic_nnt} {interval_t}interval(s).\n'
                          f'{counts_remain} counts remaining until exit.')
                if self.tic_nnt == 1:
                    # print(f'\r{self.del_line}{report}')
                    print(f'\x1b[1F{self.del_line}{report}')
                if self.tic_nnt > 1:
                    print(f'\x1b[2F{self.del_line}{report}')
                if self.share.setting['do_log'].get() == 1:
                    report_cleaned = self.ansi_esc.sub('', report)
                    logging.info(report_cleaned)
                if self.notrunning is True:
                    report = (f'\n{time_now};'
                              ' *** Check whether tasks are running. ***\n')
                    print(f'\x1b[1F{self.del_line}{report}')
                    if self.share.setting['do_log'].get() == 1:
                        logging.info(report)
            
            elif self.count_new > 0 and self.notrunning is False:
                self.tic_nnt -= self.tic_nnt
                tt_total, tt_mean, tt_sd, tt_min, tt_max = self.get_timestats(
                    self.count_new, self.ttimes_new).values()
                tt_total, tt_mean, tt_sd, tt_min, tt_max = self.share.gettimestats('interval').values()
                # TODO: Do this instead for textvariables:
                #  interval_dict = self.get_timestats(self.count_new, self.ttimes_new)
                #         self.share.tt_mean.set(interval_dict['tt_mean'])
                # TODO: recode for gui and logging option, as for start report
                report = (
                    # f'\n{time_now}; Tasks reported in the past {INTERVAL_M}m:'
                    f'{time_now}; Tasks reported in the past {interval_t}:'
                    f' {self.blue}{self.count_new}{self.undo_color}\n'
                    f'{self.indent}Task Time: mean {self.blue}{tt_mean}{self.undo_color},'
                    f' range [{tt_min} - {tt_max}],\n'
                    f'{self.bigindent}stdev {tt_sd}, total {tt_total}\n'
                    f'{self.indent}Total tasks in queue: {self.num_tasks}\n\n'
                    f'{counts_remain} counts remaining until exit.'
                )
                # Need to overwrite 'counts remaining' line of previous report
                #   with the timer bar, so move cursor 1 line up & delete.
                print(f'\x1b[1F{self.del_line}{report}')
                if self.share.setting['do_log'].get() == 1:
                    report_cleaned = self.ansi_esc.sub('', report)
                    logging.info(report_cleaned)
            
            elif self.count_new > 0 and self.notrunning is True:
                report = (f'\n{time_now};'
                          f' *** Check whether tasks are running. ***\n')
                print(f'\x1b[1F{self.del_line}{report}')
                if self.share.setting['do_log'].get() == 1:
                    logging.info(report)
            
            elif self.count_new > 0 and self.notrunning is True:
                report = (f'\n{time_now};'
                          f' *** Check whether tasks are running. ***\n')
                # print(f'\r\x1b[A{self.del_line}{report}')
                print(f'\x1b[1F{self.del_line}{report}')
                if self.share.setting['do_log'].get() == 1:
                    logging.info(report)
            self.summary_reports(loop_num, self.ttimes_smry)
    
    def summary_reports(self, loop_num: int, ttimes_smry: list) -> None:
        """
        Report task counts time stats summaries at timed intervals.

        :param loop_num: The for loop number from interval_reports().
        :param ttimes_smry: Cumulative list of task times from interval_reports()
        :return: Terminal printed reports. Data for GUI display. Log write if
        optioned.
        """
        # Get values from CountViewer.settings()
        summary_m = self.get_min(self.share.setting['summary_t'].get())
        interval_m = int(self.share.setting['interval_t'].get()[:-1])
        summary_factor = summary_m // interval_m
        if (loop_num + 1) % summary_factor == 0 and self.notrunning is False:
            # Need unique tasks for stats and counting.
            self.share.ttimes_uniq = set(ttimes_smry)
            self.share.count_sumry = len(self.ttimes_uniq)
            
            # tt_total, tt_mean, tt_sd, tt_min, tt_max = \
            #     self.get_timestats(count_sumry, self.ttimes_uniq).values()
            tt_total, tt_mean, tt_sd, tt_min, tt_max = self.share.gettimestats('summary').values()
            # TODO: recode for gui and logging option, as for start report
            summary_t = self.share.setting['summary_t'].get()
            report = (
                f'{self.time_now}; '
                f'{self.orng}>>> SUMMARY:{self.undo_color} Count for the past'
                f' {summary_t}: {self.blue}{self.share.count_sumry}{self.undo_color}\n'
                f'{self.indent}Task Time: mean {self.blue}{tt_mean}{self.undo_color},'
                f' range [{tt_min} - {tt_max}],\n'
                f'{self.bigindent}stdev {tt_sd}, total {tt_total}\n\n\n'
            )
            print(f'\r{self.del_line}{report}')
            if self.share.setting['do_log'].get() == 1:
                report_cleaned = self.ansi_esc.sub('', report)
                logging.info(report_cleaned)
            
            # Need to reset data lists, in interval_reports(), for the next
            # summary interval.
            self.ttimes_smry.clear()
            self.ttimes_uniq.clear()

    @staticmethod
    def get_min(time_string: str) -> int:
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
        return ('Enter secs as integer, time_format (format) as either'
                f" 'std' or 'short'. Arguments as entered: secs={secs}, "
                f"format={time_format}.")
    
    def intvl_timer(self, interval: int) -> None:
        """Provide sleep intervals and display countdown timer.

        :param interval: Minutes between task counts; range[5-60, by 5's]
        :return: A terminal/console graphic that displays time remaining.
        """
        # Idea for development from
        # https://stackoverflow.com/questions/3160699/python-progress-bar
        # /3162864
        
        # Initial timer bar length; 60 fits well with clock times.
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
        
        # Needed for Windows Cmd Prompt ANSI text formatting. shell=True is
        # safe because there is no external input.
        if sys.platform[:3] == 'win':
            subprocess.call('', shell=True)
        
        # Not +1 in range because need only to sleep to END of interval.
        for i in range(bar_len):
            remain_bar = prettybar[i:]
            num_segments = len(remain_bar)
            print(f"\r{self.del_line}{whitexx_on_red}"
                  f"{self.format_sec(remain_s, 'short')}{remain_bar}"
                  f"{self.undo_color}|< ~time to next count", end='')
            if num_segments == 1:
                print(f"\r{self.del_line}{whitexx_on_grn}"
                      f"{self.format_sec(remain_s, 'short')}{remain_bar}"
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
        :return: Dict keys: tt_total, tt_mean, tt_sd, tt_min, tt_max;
                 Dict values as: 00:00:00.
        """
        # NOTE: If change item number or order, statements that unpack values
        #  will need editing.
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


class CountController(tk.Tk):
    """
    The Controller through which other MVC Classes can interact.
    """
    
    def __init__(self):
        super().__init__()
        
        # Need to fix window size to prevent an annoying window redraw each time
        #   font size changes the width of the result Entry() widgets and Frame().
        # Pixels here are set to fit a 52 character width, W, Entry() and are
        #   OS-specific. (Var constant W = 52 is arbitrary, but I like it.)
        # Need OS-specific master window sizes b/c of different default font widths.
        # TODO: adjust OS-specific min/max size.
        if MY_OS == 'lin':
            self.minsize(550, 390)
            self.maxsize(780, 390)
        elif MY_OS == 'win':
            self.minsize(550, 390)
            self.maxsize(702, 380)
        elif MY_OS == 'dar':
            self.minsize(550, 390)
            self.maxsize(745, 380)
        
        # pylint: disable=assignment-from-no-return
        container = tk.Frame(self).grid()
        CountViewer(master=container, share=self)
    
    def defaultsettings(self) -> None:
        """
        Is called for start report and whenever user opts to
        change back to default run parameters: report interval,
        summary interval, counting limit, log file option.
        """
        CountModeler(share=self).default_settings()

    def getmin(self, timestring: str) -> int:
        """
        Converts a time string into minutes.
        
        :param timestring: value+unit, e.g. 60m, 12h, or 2d.
        :return: converted minutes as integer
        """
        return CountModeler(share=self).get_min(timestring)

    def getstartdata(self, *args) -> None:
        """
        Is called from Viewer.show_startdata()
        where get_timestats() returns dictionary of time statistics.
        """
        CountModeler(share=self).get_start_data()

    def getintervaldata(self, *args) -> None:
        """
        Is called from Viewer.show_intervaldata()
        where get_timestats() returns dictionary of time statistics.
        """
        CountModeler(share=self).get_interval()
    # def gettimestats(self, *args) -> None:
    #     """
    #     Is called from Modeler.
    #     get_timestats() returns dictionary of task time metrics and stats.
    #
    #     """
    #     CountModeler(share=self).get_timestats(self.count_start, self.ttimes_start)
    #
    #     #  'start': self.share.count_start, self.share.ttimes_start)
    #     # 'interval': self.share.count_new, self.share.ttimes_new)
    #     # 'summary': self.share.count_sumry, self.share.ttimes_uniq)

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
        """A silly diversion; called from Help menu.

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
        ]
        praise = random.choice(compliments)
        self.share.compliment_txt.config(text=praise)
        
        def refresh():
            self.share.compliment_txt.config(text="")
            app.update_idletasks()
        
        self.share.compliment_txt.after(2222, refresh)
    
    # TODO:
    @staticmethod
    def about() -> None:
        """
        Basic information for count-tasks; called from GUI Help menu.

        :return: Information window.
        """
        # msg separators use em dashes.
        about = ("""
CountBOINCtasks provides task counts and time statistics at set
intervals for tasks that have been reported to BOINC servers.
Download the most recent version from:
https://github.com/csecht/CountBOINCtasks
————————————————————————————————————————————————————————————————————
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.\n
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.\n
You should have received a copy of the GNU General Public License
along with this program. If not, see https://www.gnu.org/licenses/
————————————————————————————————————————————————————————————————————\n
                Author:     cecht, BOINC ID: 990821
                Copyright:  Copyright (C) 2020 C. Echt
                Credits:    Inspired by rickslab-gpu-utils,
                            Keith Myers - Testing, debug
                Development Status: 4 - Beta
                Version:    """)
        
        num_lines = about.count('\n')
        aboutwin = tk.Toplevel()
        aboutwin.minsize(570, 460)
        aboutwin.title('About count-tasks')
        colour = ['SkyBlue4', 'DarkSeaGreen4', 'DarkGoldenrod4', 'DarkOrange4',
                  'grey40', 'blue4', 'navy', 'DeepSkyBlue4', 'dark slate grey',
                  'dark olive green', 'grey2', 'grey25', 'DodgerBlue4',
                  'DarkOrchid4']
        bkg = random.choice(colour)
        abouttxt = tk.Text(aboutwin, width=72, height=num_lines + 2,
                           background=bkg, foreground='grey98',
                           relief='groove', borderwidth=5, padx=5)
        abouttxt.insert('1.0', about + PROGRAM_VER)
        # Center text preceding the Author, etc. details.
        abouttxt.tag_add('text1', '1.0', float(num_lines - 5))
        abouttxt.tag_configure('text1', justify='center')
        abouttxt.pack()


if __name__ == "__main__":
    try:
        app = CountController()
        app.title("Count BOINC tasks")
        app.mainloop()
    except KeyboardInterrupt:
        exit_msg = (f'\n\n  *** Interrupted by user ***\n'
                    f'  Quitting now...{datetime.now()}\n\n')
        sys.stdout.write(exit_msg)
        logging.info(msg=exit_msg)
