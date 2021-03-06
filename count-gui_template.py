#!/usr/bin/env python3

"""
A test GUI for count-tasks.py. Data are not live.

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

import argparse
import logging
import random
import re
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
    from tkinter.scrolledtext import ScrolledText
except (ImportError, ModuleNotFoundError) as error:
    print('GUI requires tkinter, which is included with Python 3.7 and higher')
    print('Install 3.7+ or re-install Python and include Tk/Tcl.')
    print(f'See also: https://tkdocs.com/tutorial/install.html \n{error}')

__author__ =    'cecht, BOINC ID: 990821'
__copyright__ = 'Copyright (C) 2020 C. Echt'
__credits__ =   ['Inspired by rickslab-gpu-utils',
                 'Keith Myers - Testing, debug']
__license__ =   'GNU General Public License'
__version__ =   '0.5x'
__program_name__ = 'count-tasks.py'
__maintainer__ = 'cecht'
__docformat__ = 'reStructuredText'
__status__ =    'Development Status :: 5 - ALPHA'

BC = boinc_command.BoincCommand()
# # Assume log file is in the CountBOINCtasks-master folder.
# # Not sure what determines the relative Project path.
# #    Depends on copying the module?
LOGPATH = Path('count-tasks_log.txt')
# LOGPATH = Path('../count-tasks_log.txt')
ICONPATH = Path('Python-icon.ico')
BKUPFILE = 'count-tasks_log(copy).txt'
PROGRAM_VER = '0.5x'
GUI_TITLE = __file__

# Here logging is lazily employed to manage the file of report data.
logging.basicConfig(filename=str(LOGPATH), level=logging.INFO,
                    filemode="a", format='%(message)s')

# TODO: Convert to MVC architecture.
# TODO: Add total tasks in queue (from count-tasks.py v.0.4.14)


# The tkinter gui engine that runs as main thread.
class CountGui:
    """
    GUI displays only start data. Interval data not live.
    """
    # pylint: disable=too-many-instance-attributes
# TODO: Add pretty icon to data_intervals window. These variations don't work:
    # icon = tk.PhotoImage(Image.open('Python-icon.png'))
    # icon.show() # Shows a stand-alone image, so file is okay.
    # mainwin.iconphoto(False, tk.PhotoImage(file='Python-icon.png'))
    # icon = tk.PhotoImage(file='Python-icon.png')
    # # icon.image = icon
    # mainwin.iconphoto(True, icon)
    # mainwin.tk.call('wm', 'iconphoto', mainwin._w,
    #                 tk.PhotoImage(file='Python-icon.png'))

    def __init__(self, mainwin: tk.Tk):

        # self.datadict = datadict
        self.mainwin = mainwin

        self.row_fg = None
        self.data_bg = None
        self.mainwin_bg = None
        self.dataframe = None

        self.mainwin_cfg()
        self.mainwin_widgets()

        # Label fg configuration variables
        self.emphasize = 'grey90'
        self.highlight = 'gold'
        self.deemphasize = 'grey60'

        # Starting data report var
        self.count_lim = None
        self.time_start = None
        self.intvl_str = None
        self.sumry_intvl = None
        self.count_start = None
        self.interval = None

        # Common data reports var
        self.tt_mean = None
        self.tt_sd = None
        self.tt_lo = 'None'  # Need to concatenate lo & hi as strings.
        self.tt_hi = 'None'
        self.tt_sum = None
        self.time_now = None
        self.count_next = "timer not working"
        self.count_remain = None

        # Unique to interval data report var
        self.count_now = None
        self.tic_nnt = None

        # Unique to summary data report var
        self.count_uniq = None

        # Label names used to show data. _suml are for show_sumrydata()
        self.time_start_l = tk.Label(self.dataframe, bg=self.data_bg,
                                     fg='grey90')
        self.intvl_str_l = tk.Label(self.dataframe, width=20, relief='groove',
                                    borderwidth=2, bg=self.data_bg)
        self.sumry_intvl_l = tk.Label(self.dataframe, width=20, relief='groove',
                                      borderwidth=2, bg=self.data_bg)
        self.count_start_l = tk.Label(self.dataframe, bg=self.data_bg)
        self.count_now_l = tk.Label(self.dataframe, bg=self.data_bg)
        self.count_uniq_l = tk.Label(self.dataframe, bg=self.data_bg)
        self.tt_mean_l = tk.Label(self.dataframe, bg=self.data_bg)
        self.tt_sd_l = tk.Label(self.dataframe, bg=self.data_bg)
        self.time_range_l = tk.Label(self.dataframe, bg=self.data_bg)
        self.tt_sum_l = tk.Label(self.dataframe, bg=self.data_bg)
        self.tt_mean_suml = tk.Label(self.dataframe, bg=self.data_bg)
        self.tt_sd_suml = tk.Label(self.dataframe, bg=self.data_bg)
        self.time_range_suml = tk.Label(self.dataframe, bg=self.data_bg)
        self.tt_sum_suml = tk.Label(self.dataframe, bg=self.data_bg)

        # Could use style with ttk.Label to remove redundancies, but,
        # that requires changing fg to foreground in all the show_() methods.
        # style_data = ttk.Style(self.dataframe)
        # style_data.configure('TLabel', background=self.data_bg)
        # self.count_start_l =    ttk.Label()
        # self.count_now_l =      ttk.Label()
        # self.count_uniq_l =     ttk.Label()
        # self.tt_mean_l =        ttk.Label()
        # self.tt_sd_l =          ttk.Label()
        # self.time_range_l =     ttk.Label()
        # self.tt_sum_l =         ttk.Label()
        # self.tt_mean_suml =     ttk.Label()
        # self.tt_sd_suml =       ttk.Label()
        # self.time_range_suml =  ttk.Label()
        # self.tt_sum_suml =      ttk.Label()

        style_main = ttk.Style(self.mainwin)
        style_main.configure('TLabel', background=self.mainwin_bg,
                             foreground=self.row_fg)
        self.time_now_l = ttk.Label()
        self.count_lim_l = ttk.Label()
        self.count_next_l = ttk.Label()
        self.count_remain_l = ttk.Label()

        # Settings variables with default parser args values.
        self.intvl_arg = tk.IntVar(value=60)
        self.sumry_arg = tk.StringVar(value='1d')
        self.cycles_arg = tk.IntVar(value=1008)

        # stubdata are only for testing GUI layout.
        # self.set_stubdata()

        # The data dictionary is from data_intervals(). set_startdata includes "config()"
        # and calls show_startdata().
        # Set starting data config are same style as config_intvldata.
        print('\n*** Close program through the GUI, not the Terminal ***'
              '\n*** NOTE: Interval counts not working in this version. ***\n')
        self.set_startdata()

        # tkinter's infinite event loop
        # "Always call mainloop as the last logical line of code in your
        # program." per Bryan Oakly:
        # https://stackoverflow.com/questions/29158220/tkinter-understanding-mainloop
        # self.mainwin.mainloop()
        # ^^ NOTE: mainloop is may be instantiated in show_startdata(),
        #  for testing purposes. Or may be in if __name__....

    def mainwin_cfg(self) -> None:
        """
        Configure colors, key binds & basic behavior of data_intervals Tk window.
        """
        # Needed for data readability in smallest resized dataframe. Depends
        #   on platform; set for Linux with its largest relative font size.
        self.mainwin.minsize(466, 390)
        self.mainwin.title(GUI_TITLE)
        # Window icon .ico does not show on Linux Ubuntu, but does on Windows.
        # if sys.platform[:3] == 'win':
        if sys.platform.startswith('win'):
            self.mainwin.iconbitmap(ICONPATH)

        # Set colors for row labels and data display.
        # http://www.science.smith.edu/dftwiki/index.php/Color_Charts_for_TKinter
        self.row_fg = 'LightCyan2'  # foreground for row labels
        self.data_bg = 'grey40'  # background for data labels and frame
        # window background color, also used for some labels.
        self.mainwin_bg = 'SkyBlue4'
        self.mainwin.configure(bg=self.mainwin_bg)

        # Theme controls entire window theme, but only for ttk.Style objects.
        # Options: classic, alt, clam, default, aqua(MacOS only)
        ttk.Style().theme_use('alt')

        self.mainwin.bind("<Escape>", lambda q: self.quitgui())
        self.mainwin.bind("<Control-q>", lambda q: self.quitgui())
        self.mainwin.bind("<Control-C>", lambda q: self.compliment())
        self.mainwin.bind("<Control-l>", lambda q: self.show_log())

        # Make data rows and columns stretch with window drag size.
        # Don't vertically stretch separator rows.
        rows2config = (2, 3, 4, 5, 6, 7, 8, 10, 11, 12)
        for _r in rows2config:
            self.mainwin.rowconfigure(_r, weight=1)

        self.mainwin.columnconfigure(1, weight=1)
        self.mainwin.columnconfigure(2, weight=1)

        # Set up frame to display data. Putting frame here instead of in
        # mainwin_widgets gives proper alignment of row headers and data.
        self.dataframe = tk.LabelFrame(self.mainwin, borderwidth=3,
                                       relief='sunken',
                                       background=self.data_bg)
        self.dataframe.grid(row=2, column=1, rowspan=7, columnspan=2,
                            padx=(5, 10), sticky=tk.NSEW)
        framerows = (2, 3, 4, 5, 6, 7, 8)
        for row in framerows:
            self.dataframe.rowconfigure(row, weight=1)

        self.dataframe.columnconfigure(1, weight=1)
        self.dataframe.columnconfigure(2, weight=1)

        # Fill in headers for data rows.
        row_header = {
                    'Counting since':     2,
                    'Count interval':     3,
                    '# tasks reported':   4,
                    'Task times:  mean':  5,
                    'stdev':              6,
                    'range':              7,
                    'total':              8,
                    'Last count was:':    10,
                    '# counts to go:':    11,
                    'Next count in:':     12
                     }
        for header, rownum in row_header.items():
            tk.Label(self.mainwin, text=f'{header}',
                     bg=self.mainwin_bg, fg=self.row_fg
                     ).grid(row=rownum, column=0, padx=(5, 0), sticky=tk.E)

    def mainwin_widgets(self) -> None:
        """
        Layout menus, buttons, separators, row labels in main window.
        """

        # creating a menu instance
        menu = tk.Menu(self.mainwin)
        self.mainwin.config(menu=menu)

        # Add pull-down menus
        file = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="File", menu=file)
        file.add_command(label="Backup log file", command=self.backup_log)
        file.add_command(label='Settings...', command=self.settings)
        file.add_separator()
        file.add_command(label="Quit", command=self.quitgui,
                         accelerator="Ctrl+Q")

        view = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="View", menu=view)
        view.add_command(label="Log file", command=self.show_log,
                         accelerator="Ctrl+L")

        help_menu = tk.Menu(menu, tearoff=0)
        menu. add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Tips", state=tk.DISABLED)
        help_menu.add_command(label="Compliment", command=self.compliment,
                              accelerator="Ctrl+Shift+C")
        help_menu.add_command(label="About", command=self.about)

        # Create button widgets:
        style_sep = ttk.Style(self.mainwin)
        style_sep.configure('TButton', background='grey80', anchor='center')

        view_log_b = ttk.Button(text='View log file',
                                command=self.show_log)
        intvl_b = ttk.Button(text='Interval focus',
                             command=self.show_intvldata)
        sumry_b = ttk.Button(text='Summary focus',
                             command=self.show_sumrydata)
        quit_b = ttk.Button(text="Quit",
                            command=self.quitgui)
        # Button used only to test progressbar.
        test_b = ttk.Button(text="Run test bar",
                            command=self.increment_prog)

        view_log_b.grid(row=0, column=0, padx=5, pady=5)
        intvl_b.grid(row=0, column=1, padx=0, pady=5)
        sumry_b.grid(row=0, column=2, padx=(0, 25), pady=5)
        quit_b.grid(row=12, column=2, padx=5, sticky=tk.E)
        test_b.grid(row=11, column=2, padx=5, sticky=tk.E)

        # For colored separators, use ttk.Frame instead of ttk.Separator.
        # Initialize then configure style for separator color.
        style = ttk.Style()
        style.configure('TFrame', background=self.mainwin_bg)
        sep1 = ttk.Frame(self.mainwin, relief="raised", height=6)
        sep2 = ttk.Frame(self.mainwin, relief="raised", height=6)
        sep1.grid(column=0, row=1, columnspan=5,
                  padx=5, pady=(2, 5), sticky=tk.EW)
        sep2.grid(column=0, row=9, columnspan=5,
                  padx=5, pady=(6, 6), sticky=tk.EW)

        # Trial feature:
        # TODO: Integrate Progressbar widget with count-tasks intvl_timer.
        self.progress = ttk.Progressbar(self.mainwin, orient=tk.HORIZONTAL,
                                        length=100, mode='determinate')
        self.progress.grid(row=13, column=0, columnspan=3,
                           padx=5, pady=5, sticky=tk.EW)

    def set_stubdata(self) -> None:
        """
        Test data for GUI table layout.

        :return: Data for assigning and updating dataframe labels.
        """

        # Starting report
        self.count_lim = '1008'
        self.time_start = '2020-Nov-10 10:00:10'
        self.intvl_str = '60m'
        self.sumry_intvl = '1d'
        self.count_start = '24'

        # Common data reports
        self.tt_mean = '00:25:47'
        self.tt_sd = '00:00:26'
        self.tt_lo = '00:17:26'
        self.tt_hi = '00:25:47'
        self.tt_sum = 'All data are stubs'
        self.time_now = '2020-Nov-17 11:14:25'
        self.count_next = '27m'
        self.count_remain = '1000'

        # Interval data report
        self.count_now = '21'
        # self.tic_nnt = 0

        # Summary data report
        self.count_uniq = '123'

        self.show_startdata()

    # Set methods: use data from data_intervals().
    def set_startdata(self) -> None:
        """
        Set data label text variables with starting data.
        """

        startdata = {**data_intervals()}  # <-** ad hoc test return function
        self.time_start = startdata['time_start']
        self.intvl_str = startdata['intvl_str']
        self.interval = startdata['intvl_int']
        self.sumry_intvl = startdata['sumry_intvl']
        self.count_start = startdata['count_start']
        self.tt_mean = startdata['tt_mean']
        self.tt_hi = startdata['tt_hi']
        self.tt_lo = startdata['tt_lo']
        self.tt_sd = startdata['tt_sd']
        self.tt_sum = startdata['tt_sum']
        self.count_lim = startdata['count_lim']

        self.show_startdata()

    def set_intvldata(self, datadict: dict) -> None:
        """
        Set interval data from count-tasks data_intervals().

        :param datadict: Dict of report data vars with matching keywords.
        :return: Interval values for datatable labels.
        """

        self.time_now = datadict['time_now']
        self.count_now = datadict['count_now']
        self.tt_mean = datadict['tt_mean']
        self.tt_lo = datadict['tt_lo']
        self.tt_hi = datadict['tt_hi']
        self.tt_sd = datadict['tt_sd']
        self.tt_sum = datadict['tt_sum']
        self.count_remain = datadict['count_remain']

        self.show_intvldata()

    def set_sumrydata(self, datadict: dict) -> None:
        """
        Set summary data from count-tasks data_intervals().

        :param datadict: Dict of report data vars with matching keywords.
        :return: Summary values for datatable labels.
        """

        self.time_now = datadict['time_now']
        self.count_uniq = datadict['count_uniq']
        self.tt_mean = datadict['tt_mean']
        self.tt_hi = datadict['tt_hi']
        self.tt_lo = datadict['tt_lo']
        self.tt_sd = datadict['tt_sd']
        self.tt_sum = datadict['tt_sum']

        self.show_sumrydata()

    # Show methods: define and display labels for data.
    def show_startdata(self) -> None:
        """
        Show starting count-tasks data labels in GUI window.

        :return: Starting BOINC and count-tasks data, for the past hour.
        """

        # Starting datetime and report times; invariant throughout counts.
        self.time_start_l.config(text=self.time_start)
        self.intvl_str_l.config(text=self.intvl_str, fg=self.emphasize)
        self.sumry_intvl_l.config(text=self.sumry_intvl, fg=self.deemphasize)

        # Starting count data and times (from past boinc-client hour).
        time_range = self.tt_lo + ' -- ' + self.tt_hi

        self.count_start_l.config(text=self.count_start, fg=self.highlight)
        self.tt_mean_l.config(text=self.tt_mean, fg=self.highlight)
        self.tt_sd_l.config(text=self.tt_sd, fg=self.emphasize)
        self.time_range_l.config(text=time_range, fg=self.emphasize)
        self.tt_sum_l.config(text=self.tt_sum, fg=self.emphasize)

        # Previous and until task count times.
        self.time_now_l.config(text='The most recent 1 hr BOINC report')
        self.count_lim_l.config(text=self.count_lim)
        self.count_next_l.config(text=self.count_next)

        # Place labels in row,column positions.
        self.time_start_l.grid(row=2, column=1, padx=10, sticky=tk.EW,
                               columnspan=2)
        self.intvl_str_l.grid(row=3, column=1, padx=10, sticky=tk.EW)
        self.sumry_intvl_l.grid(row=3, column=2, padx=(0, 10), sticky=tk.EW)
        self.count_start_l.grid(row=4, column=1, padx=10, sticky=tk.EW)
        self.tt_mean_l.grid(row=5, column=1, padx=10, sticky=tk.EW)
        self.tt_sd_l.grid(row=6, column=1, padx=10, sticky=tk.EW)
        self.time_range_l.grid(row=7, column=1, padx=10, sticky=tk.EW)
        self.tt_sum_l.grid(row=8, column=1, padx=10, sticky=tk.EW)

        self.time_now_l.grid(row=10, column=1, padx=3, sticky=tk.W,
                             columnspan=2)
        self.count_lim_l.grid(row=11, column=1, padx=3, sticky=tk.W)
        self.count_next_l.grid(row=12, column=1, padx=3, sticky=tk.W)

    def show_intvldata(self) -> None:
        """
        Show interval count-tasks data in GUI window.

        :return: The most recent BOINC and count-tasks data.
        """
        # show_updatedata includes the interval and summary data columns.
        # Make a separate show_sumrydata() method?
        # Both reports are triggered by a common count-tasks interval event.
        #

        # Count and summary interval times
        time_range = self.tt_lo + ' -- ' + self.tt_hi

        self.intvl_str_l.config(fg=self.emphasize)
        self.sumry_intvl_l.config(fg=self.deemphasize)

        # Interval data, column1
        self.count_now_l.config(text=self.count_now, fg=self.highlight)
        self.tt_mean_l.config(text=self.tt_mean, fg=self.highlight)
        self.tt_sd_l.config(text=self.tt_sd, fg=self.emphasize)
        self.time_range_l.config(text=time_range, fg=self.emphasize)
        self.tt_sum_l.config(text=self.tt_sum, fg=self.emphasize)

        # Summary data, column2, deemphasize font color
        self.count_uniq_l.config(fg=self.deemphasize)
        self.tt_mean_suml.config(fg=self.deemphasize)
        self.tt_sd_suml.config(fg=self.deemphasize)
        self.time_range_suml.config(fg=self.deemphasize)
        self.tt_sum_suml.config(fg=self.deemphasize)

        # Previous and until task count times.
        self.count_now_l.config(text=self.count_now)
        self.time_now_l.config(text=self.time_now)
        self.count_next_l.config(text=self.count_next)

        # Place new labels (not in show_startdata) in row,column positions.
        # Also place labels whose font emphasis needs to change. ???
        self.count_now_l.grid(row=4, column=1, padx=10, sticky=tk.EW)
        self.count_remain_l.grid(row=11, column=1, padx=3, sticky=tk.W)
        self.time_now_l.grid(row=10, column=1, padx=3, sticky=tk.W,
                             columnspan=2)

    def show_sumrydata(self) -> None:
        """
        Show interval and summary count-tasks data in GUI window.

        :return: The most recent BOINC and count-tasks data.
        """
        # show_updatedata includes the interval and summary data columns.
        # Make a separate show_sumrydata() method?
        # Both reports are triggered by a common count-tasks interval event.
        #

        # Count and summary interval times
        time_range = self.tt_lo + ' -- ' + self.tt_hi

        self.intvl_str_l.config(fg=self.deemphasize)
        self.sumry_intvl_l.config(fg=self.emphasize)

        # Summary data, column2, emphasize font color
        self.count_uniq_l.config(text=self.count_uniq, fg=self.highlight)
        self.tt_mean_suml.config(text=self.tt_mean, fg=self.highlight)
        self.tt_sd_suml.config(text=self.tt_sd, fg=self.emphasize)
        self.time_range_suml.config(text=time_range, fg=self.emphasize)
        self.tt_sum_suml.config(text=self.tt_sum, fg=self.emphasize)

        # Interval data, column1, deemphasize font color
        self.count_start_l.config(text="")
        self.count_now_l.config(fg=self.deemphasize)
        self.tt_mean_l.config(fg=self.deemphasize)
        self.tt_sd_l.config(fg=self.deemphasize)
        self.time_range_l.config(fg=self.deemphasize)
        self.tt_sum_l.config(fg=self.deemphasize)

        # Previous and until task count times.  NECESSARY? b/c dupl of intvl?
        self.count_now_l.config(text=self.count_now)
        self.time_now_l.config(text=self.time_now)
        self.count_next_l.config(text=self.count_next)

        # Place labels in row,column positions.
        self.count_uniq_l.grid(row=4, column=2, padx=(0, 10), sticky=tk.EW)
        self.tt_mean_suml.grid(row=5, column=2, padx=10, sticky=tk.EW)
        self.tt_sd_suml.grid(row=6, column=2, padx=10, sticky=tk.EW)
        self.time_range_suml.grid(row=7, column=2, padx=10, sticky=tk.EW)
        self.tt_sum_suml.grid(row=8, column=2, padx=10, sticky=tk.EW)

        self.time_now_l.grid(row=10, column=1, padx=3, sticky=tk.W,
                             columnspan=2)
        self.count_remain_l.grid(row=11, column=1, padx=3, sticky=tk.W)
        self.count_next_l.grid(row=12, column=1, padx=3, sticky=tk.W)

    # Methods for menu items and keybinds.
    def quitgui(self) -> None:
        """Safe and informative exit from the program.
        """
        # For aesthetics, clear the persistent timer line; timer will be
        # redrawn (as threaded) following the print message.
        # Move cursor to beginning of timer line, erase the line, then print.
        print('\r\x1b[K'
              '\n  --- User has quit the count-tasks GUI. Scheduled counts '
              'continue... ---'
              '\n  --- To exit from scheduled task counts, use Ctrl+C. ---\n')
        self.mainwin.destroy()

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
        # icon = tk.PhotoImage(file='unused_bits/tiny_icon.png')
        # icon.image = icon
        # aboutwin.iconphoto(True, icon)
        # Minsize needed for MacOS where Help>About opens tab in mainwin.
        #   Gives larger MacOS mainwin when tab is closed, but, oh well.
        aboutwin.minsize(570, 460)
        aboutwin.title('About count-tasks')
        # aboutimg = tk.PhotoImage(file='about.png')  # or 'about.png'
        # aboutimg.image = aboutimg  # Need to anchor the image for it to display.
        # tk.Label(aboutwin, image=aboutimg).grid(row=0, column=0, padx=5, pady=5)
        colour = ['SkyBlue4', 'DarkSeaGreen4', 'DarkGoldenrod4', 'DarkOrange4',
                  'grey40', 'blue4', 'navy', 'DeepSkyBlue4', 'dark slate grey',
                  'dark olive green', 'grey2', 'grey25', 'DodgerBlue4',
                  'DarkOrchid4']
        bkg = random.choice(colour)
        abouttxt = tk.Text(aboutwin, width=72, height=num_lines+2,
                           background=bkg, foreground='grey98',
                           relief='groove', borderwidth=5, padx=5)
        abouttxt.insert('1.0', about + PROGRAM_VER)
        # Center text preceding the Author, etc. details.
        abouttxt.tag_add('text1', '1.0', float(num_lines-5))
        abouttxt.tag_configure('text1', justify='center')
        abouttxt.pack()

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
                logtext = ScrolledText(logwin, width=79, height=30, bg='grey85',
                                       relief='raised', padx=5)
                logtext.insert(tk.INSERT, log.read())
                logtext.see('end')
                logtext.grid(row=0, column=0, sticky=tk.NSEW)
                logtext.focus_set()
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
        Copy the log file to the home folder; called from GUI File menu.

        :return: A new or overwritten backup file.
        """

        destination = Path.home() / BKUPFILE
        if Path.is_file(LOGPATH) is True:
            shutil.copyfile(LOGPATH, destination)
            success_msg = 'Log file has been copied to ' + str(destination)
            # Main window alert; needed along with notification in new window?
            # text = tk.Label(self.mainwin, text=msg, font=('default', 10),
            #                 foreground='DodgerBlue4', background='gold2',
            #                 relief='flat')
            # text.grid(row=9, column=0, columnspan=3,
            #           padx=5, pady=6,
            #           sticky=tk.EW)
            # self.mainwin.after(4000, text.destroy)

            # Need a persistent window alert.
            logwin = tk.Toplevel()
            logwin.attributes('-topmost', 1)
            logwin.title('Archive notification')
            logtext = tk.Text(logwin, width=75, height=2,
                              fg='green', bg='grey85',
                              relief='raised', padx=5)
            logtext.insert(tk.INSERT, success_msg)
            logtext.grid(row=0, column=0, sticky=tk.NSEW)
            logtext.focus_set()
        else:
            user_warn = (f'The file {LOGPATH} cannot be archived because it\n'
                         ' is not in the CountBOINCtasks-master folder.\n'
                         'Has the file been created with the --log command '
                         'line option?\nOr perhaps it has been moved?')
            print(user_warn)
            # Need a persistent window alert in addition to a terminal alert.
            logwin = tk.Toplevel()
            logwin.attributes('-topmost', 1)
            logwin.title('Archive log error')
            logtext = tk.Text(logwin, width=62, height=4,
                              fg='red', bg='grey85',
                              relief='raised', padx=5)
            logtext.insert(tk.INSERT, user_warn)
            logtext.grid(row=0, column=0, sticky=tk.NSEW)
            logtext.focus_set()

    def compliment(self) -> None:
        """
         A silly diversion; used with the 'compliment' GUI menu item.

        :return: Transient label to make one smile.
        """
        comp = ["Hey there good lookin'!", 'You are the smartest person I know.',
                'I like your hair.', 'You have such a nice smile.', 'Smart move!',
                'Blue is your color.', 'Good choice!', "That's very kind of you.",
                "Stop! You're making me blush.", 'I just love what you did.',
                'BOINC crunchers rule.', 'How witty you are!', 'Awesome!',
                'Your tastes are impeccable.', "You're incredible!",
                'You are so talented!', "I wish I'd thought of that.",
                'This is fun!', 'Get back to work.', 'Nice!', 'You saved me.',
                'You are an inspiration to us all.', "That's so funny!",
                'Show me how you do that.', 'You look great!', 'You sound great!',
                'You smell nice.', 'Great job!', 'You are a role model.',
                'I wish more people were like you.', 'We appreciate what you did.',
                'I hear people look up to you.', 'You are a really good dancer.',
                'When you speak, people listen.', 'You are a superb cruncher.',
                'You rock!', 'You nailed it!', 'That was really well done.',
                'You are amazing!', 'We need more folks like you around here.',
                'Excuse me, are you a model?', 'What a lovely laugh you have.',
                "I'm jealous of your ability.", 'Thank you so much!',
                'This would not be possible without you.', 'Way to go! Yay!',
                'Did you make that? I love it!', 'You are the best!',
                'I like what you did.', 'Whoa. Have you been working out?',
                "We can't thank you enough.", 'No, really, you have done enough.',
                "That's a good look for you.", 'I could not have done it better.',
                "I can't think of anything to say. Sorry.", 'Congratulations!',
                "Well, THAT's impressive.", 'I hear that you are the one.',
                'You excel at everything.', 'Your voice is very soothing.',
                'Is it true what people say?', 'The word is, you got it!',
                "The Nobel Committee has been trying to reach you.",
                'What makes you so successful?', "I've always looked up to you."
                ]
        txt = random.choice(comp)
        text = tk.Label(self.dataframe, text=txt,
                        # font=('default', 10),
                        foreground='DodgerBlue4',
                        background='gold2',
                        relief='flat',
                        border=0)
        text.grid(row=2, column=1, columnspan=2,
                  padx=(15, 20), sticky=tk.EW)
        # To fit well, pady ^here must match pady of the same data label row.
        self.dataframe.after(2468, text.destroy)

    # Trial features:
    def settings(self):
        """
        Test window layout for File>Settings... to change program args.

        :return: On-the-fly program parameters changes.
        """

        # Use for on-the-fly changes, or use in place of command line
        # parameters? In place of may be easier to code.
        # See: https://www.programcreek.com/python/example/104124/tkinter.ttk.Checkbutton
        # Window basics
        set_win = tk.Toplevel(relief='raised', bd=3)
        set_win.title('Settings (inactive)')
        set_win.attributes('-topmost', True)
        # set_win.call('wm', 'attributes', '.', '-topmost', '1')
        setting_bg = 'SkyBlue4'
        setting_fg = 'LightCyan2'
        set_win.configure(bg=setting_bg)
        style = ttk.Style()
        style.configure('TLabel', background=setting_bg, foreground=setting_fg)

        # Have user pick an interval time for count cycles and reports.
        intvl_time = ttk.Combobox(set_win, textvariable=self.intvl_arg,
                                  width=2)
        intvl_time['values'] = (5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60)
        intvl_time.state(['readonly'])
        intvl_time.grid(column=1, row=0)
        intvl_label1 = ttk.Label(set_win, text='Count interval')
        intvl_label1.grid(column=0, row=0, padx=5, pady=10, sticky=tk.E)
        intvl_label2 = ttk.Label(set_win, text='minutes; default 60')
        intvl_label2.grid(column=2, row=0, padx=5, pady=10, sticky=tk.W)

# https://www.geeksforgeeks.org/python-tkinter-validating-entry-widget/
# https://stackoverflow.com/questions/13340993/tkinter-entry-widget-error-if-entry-is-not-an-int
        # Have user pick a time interval for report summary statistics.
        sumry_time = ttk.Entry(set_win, textvariable=self.sumry_arg,
                               width=4)
        sumry_time.grid(column=1, row=1)
        sumry_label1 = ttk.Label(set_win, text='Summary interval')
        sumry_label1.grid(column=0, row=1, padx=(10, 5), pady=10, sticky=tk.E)
        sumry_label2 = ttk.Label(set_win, text='e.g., 12h, 7d; default 1d')
        sumry_label2.grid(column=2, row=1, padx=(5, 10), pady=10, sticky=tk.W)

        # Have user pick total number of counting cycles to run.
        cycles = ttk.Entry(set_win, textvariable=self.cycles_arg, width=4)
        cycles.grid(column=1, row=2)
        cycles_label1 = ttk.Label(set_win, text='# Count cycles')
        cycles_label1.grid(column=0, row=2, padx=5, pady=10, sticky=tk.E)
        cycles_label2 = ttk.Label(set_win, text='default 1008')
        cycles_label2.grid(column=2, row=2, padx=5, pady=10, sticky=tk.W)

        # Have user pick whether to use a log file.
        chooselog = tk.Checkbutton(set_win, bg=setting_bg, borderwidth=0)
        chooselog.grid(column=1, row=3, padx=0, sticky=tk.W)
        log_label = ttk.Label(set_win, text='Log results to file')
        log_label.grid(column=0, row=3, padx=5, pady=10, sticky=tk.E)
        # use args.log is True here, somewhere?

        # What command to use to activate settings? How to pass values to args?
        use_settings = ttk.Button(set_win, text='Confirm settings')
        use_settings.grid(column=2, row=3, padx=10, pady=10, sticky=tk.E)

    # TODO: Integrate Progressbar widget with count-tasks intvl_timer
    # Test timer for progress bar; button may be disabled.
    def increment_prog(self) -> None:
        """
        Used to test drive the Progressbar.

        :return: timing of progress bar.
        """
    # https://stackoverflow.com/questions/33768577/tkinter-gui-with-progress-bar
    # Read answer to structure bar with threading, but threading may not be good.
        # Note that this prevents all other module actions while running
        for i in range(100):
            self.progress["value"] = i + 1
            self.mainwin.update()
            time.sleep(0.1)
        self.progress["value"] = 0  # Reset bar


# Functions that are used by data_intervals().
def check_args(parameter) -> None:
    """
    Check command line --summary argument for errors.

    :param parameter: Passed from parser.add_argument 'type' call.
    :return: If no errors, return the parameter string.
    """

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
        err_msg = f'Invalid time unit: {unit} -  Use: m, h, or d'
        raise KeyError(err_msg) from err


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
    note = ('fmt_sec error: Enter secs as seconds, fmt (format) as either'
            f" 'std' or 'short'. Arguments as entered: secs={secs}, "
            f"fmt={fmt}.")
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
    return note


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
    if sys.platform.startswith('win'):
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
        time.sleep(barseg_s)


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
        mean = fmt_sec(int(stats.mean(set(taskt))), 'std')
        stdev = fmt_sec(int(stats.stdev(set(taskt))), 'std')
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


def data_intervals() -> dict:
    """
    Threaded flow for timing intervals and gathering task data.

    :rtype: object
    :return: A dictionary of data be called from CountGui
    """
    # TODO: Make gui the default (with no terminal option?)
    args.gui = True  # For testing only; True allows call to CountGui().

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
    undo_color = '\x1b[0m'  # No color, reset to system default.
    # regex from https://stackoverflow.com/questions/14693701/
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    # Needed for Windows Cmd Prompt ANSI text formatting. shell=True is safe
    # because any command string is constructed from internal input only.
    if sys.platform.startswith('win'):
        subprocess.call('', shell=True)

    # Report: start information for existing task times and counts.
    tt_sum, tt_mean, tt_sd, tt_lo, tt_hi = get_timestats(count_start,
                                                         ttimes_start).values()
    report = (f'{time_start}; Number of tasks in the most recent BOINC report:'
              f' {blue}{count_start}{undo_color}\n'
              f'{indent}Task Times: mean {blue}{tt_mean}{undo_color},'
              f' range [{tt_lo} - {tt_hi}],\n'
              f'{bigindent}stdev {tt_sd}, total {tt_sum}\n'
              f'{indent}Number of scheduled count intervals: {count_lim}\n'
              f'{indent}Timed intervals beginning now...')
    print(report)
    if args.log is True:
        report = ansi_escape.sub('', report)
        # This is proper string formatting for logging, but f-strings, as used
        # elsewhere, are fine for this program's shortcut use of logging.
        logging.info("""%s; Task counter is starting with
%scount interval (minutes): %s
%ssummary interval: %s
%smax count cycles: %s
%s""",               time_start,
                     indent, args.interval,
                     indent, args.summary,
                     indent, args.count_lim,
                     report)
    if args.gui is True:
        datadict = {'time_start':   time_start,
                    'intvl_str':    intvl_str,
                    'intvl_int':    interval_m,
                    'sumry_intvl':  sumry_intvl,
                    'count_start':  count_start,
                    'tt_mean':      tt_mean,
                    'tt_lo':        tt_lo,
                    'tt_hi':        tt_hi,
                    'tt_sd':        tt_sd,
                    'tt_sum':       tt_sum,
                    'count_lim':    count_lim}
        return datadict
        # cg = CountGui(**datadict)
        # cg.set_startdata()

# TODO: If use return to pass data tp GUI, then need separate data functions.

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
    # intvl_timer() sleeps the for loop between count cycles.
    for i in range(count_lim):
        intvl_timer(interval_m)
        # t.sleep(5)  # DEBUG; or use to bypass intvl_timer.
        time_now = datetime.now().strftime(time_fmt)
        count_remain = count_lim - (i + 1)
        # active_task_state for running tasks will be 'EXECUTING'.
        tasks_running = BC.get_tasks('active_task_state')
        notrunning = False

        if len(ttimes_now) > 0:
            ttimes_prev = ttimes_now[:]

        # Needs to be after ttimes_prev = ttimes_now[:].
        ttimes_now = BC.get_reported('elapsed time')

        if len(ttimes_now) > 0 and "EXECUTING" in tasks_running:
            ttimes_now = [task for task in ttimes_now if task not in ttimes_prev]
        # Need this check for when tasks have run out.
        elif len(ttimes_now) > 0 and "EXECUTING" not in tasks_running:
            notrunning = True

        if len(ttimes_start) > 0:
            ttimes_now = [task for task in ttimes_now if task not in ttimes_start]
            ttimes_start.clear()

        count_now = len(set(ttimes_now))
        ttimes_smry.extend(ttimes_now)

        # Report: Repeating intervals
        # Suppress full report for no new tasks, which are expected for
        # long-running tasks (b/c 60 m is longest allowed count interval).
        # Overwrite successive NNT reports for a tidy terminal window: \x1b[3A.
        if count_now == 0:
            tic_nnt += 1
            report = (f'{time_now}; '
                      f'No tasks reported in the past {tic_nnt} {interval_m}m'
                      f' interval(s).\n'
                      f'{indent}Counts remaining until exit: {count_remain}')
            if tic_nnt == 1:
                print(f'\r{del_line}{report}')
            if tic_nnt > 1:
                print(f'\r\x1b[3A{del_line}{report}')
            if args.log is True:
                logging.info(report)

        elif count_now > 0 and notrunning is False:
            tic_nnt -= tic_nnt
            tt_sum, tt_mean, tt_sd, tt_lo, tt_hi = \
                get_timestats(count_now, ttimes_now).values()
            report = (f'\n{time_now}; '
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

        elif count_now > 0 and notrunning is True:
            tic_nnt -= tic_nnt
            report = f'{time_now}; *** Check whether tasks are running. ***\n'
            print(f'\r{del_line}{report}')
            if args.log is True:
                logging.info(report)

        # Report: Summary intervals
        if (i + 1) % sumry_factor == 0 and notrunning is False:
            # Need unique tasks for stats and counting.
            ttimes_uniq = set(ttimes_smry)
            count_uniq = len(ttimes_uniq)

            tt_sum, tt_mean, tt_sd, tt_lo, tt_hi = \
                get_timestats(count_uniq, ttimes_uniq).values()
            report = (f'\n{time_now}; '
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


# Need data acquisition and timer in Thread so tkinter can run in main thread.
# TODO: reset interval and summary default times.
if __name__ == '__main__':
    # NOTE: --interval and --summary argument formats are different
    #   because summary times can be min, hr, or days, while interval times
    #   are always minutes (60 maximum).
    # NOTE: Boinc only returns tasks that were reported in past hour.
    #   Hence an --interval maximum limit to count tasks at least once per
    #   hour.
    # TODO: RESET --interval default to 60 for distribution version.
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
    parser.add_argument('--gui',
                        help='Show data in graphics window.',
                        action='store_true',
                        default=False)
    parser.add_argument('--interval',
                        help='Specify minutes between task counts'
                             ' (default: %(default)d)',
                        # default=60,
                        default=5,  # for testing
                        choices=range(5, 65, 5),
                        type=int,
                        metavar="M")
    parser.add_argument('--summary',
                        help='Specify time between count summaries,'
                             ' e.g., 12h, 7d (default: %(default)s)',
                        # default='1d',
                        default='15m',  # for testing
                        type=check_args,
                        metavar='TIMEunit')
    parser.add_argument('--count_lim',
                        help='Specify number of count reports until program'
                             ' exits (default: %(default)d)',
                        default=1008,
                        type=int,
                        metavar="N")
    args = parser.parse_args()

    # Variables to deal with parser arguments and defaults.
    count_lim = int(args.count_lim)
    interval_m = int(args.interval)
    sumry_m = get_min(args.summary)
    sumry_factor = sumry_m // interval_m
    # Variables used for CountGui() data display.
    intvl_str = f'{args.interval}m'
    sumry_intvl = args.summary

    if interval_m >= sumry_m:
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

    # interval_thread = threading.Thread(target=data_intervals, daemon=True)
    # interval_thread = threading.Thread(target=data_intervals)
    # interval_thread.start()  # Not necessary here (or anywhere?)
    root = tk.Tk()
    CG = CountGui(root)
    root.mainloop()
    # try:
    #     root.mainloop()
    #     # interval_thread.join()
    # except KeyboardInterrupt:
    #     exit_msg = '\n\n  *** Interrupted by user. Quitting now... \n\n'
    #     sys.stdout.write(exit_msg)
    #     logging.info(msg=f'\n{datetime.now()}: {exit_msg}')
