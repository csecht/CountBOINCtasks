#!/usr/bin/env python3
"""
A dummy module; a template GUI for displaying count-tasks data.

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

import random
import shutil
import time

from pathlib import Path
# from COUNTmodules import boinc_command

try:
    import tkinter as tk
    import tkinter.ttk as ttk
    from tkinter.scrolledtext import ScrolledText
except (ImportError, ModuleNotFoundError) as err:
    print('GUI requires tkinter, which is included with Python 3.7 and higher')
    print('Install 3.7+ or re-install Python and include Tk/Tcl.')
    print(f'See also: https://tkdocs.com/tutorial/install.html \n{err}')

# # Assume log file is in the CountBOINCtasks-master folder.
# # Not sure what determines the relative Project path.
# #    Depends on copying the module?
LOGPATH = Path('../count-tasks_log.txt')
# LOGPATH = Path('count-tasks_log.txt')
BKUPFILE = 'count-tasks_log(copy).txt'
PROGRAM_VER = '0.5'
TITLE = 'stub count-tasks data'

# __author__      = 'cecht, BOINC ID: 990821'
# __copyright__   = 'Copyright (C) 2020 C. Echt'
# __credits__     = ['Inspired by rickslab-gpu-utils',
#                    'Keith Myers - Testing, debug']
# __license__     = 'GNU General Public License'
# __program_name__ = 'count-tasks.py'
# __version__     = SCRIPT_VER
# __maintainer__  = 'cecht'
# __docformat__   = 'reStructuredText'
# __status__      = 'Development Status :: 4 - Beta'

# https://python.readthedocs.io/en/stable/library/tk.html
# Original code source:
# https://pythonprogramming.net/python-3-tkinter-basics-tutorial/


class CountGui:
    """
    A GUI window to display data from count-tasks.
    """
    # pylint: disable=too-many-instance-attributes

    mainwin = tk.Tk()
    mainwin.title(TITLE)

    def __init__(self, **kwargs):

        self.datadict = kwargs

        self.row_fg = None
        self.data_bg = None
        self.mainwin_bg = None
        self.dataframe = None

        self.mainwin_cfg()
        self.mainwin_widgets()

        # Mutable color variables used for emphasizing different data
        # categories via buttons.
        self.intvl_t    = ['']
        self.intvl_main = ['']
        self.intvl_stat = ['']
        self.sumry_t    = ['']
        self.sumry_main = ['']
        self.sumry_stat = ['']

        # Data var names=None are used only in stubdata().
        # _sv can be refactored w/o suffix and assigned as StringVar
        # objects in a for loop with .append from a list or dictionary?
        # Starting data report var
        self.count_lim = None
        self.time_start = None
        self.count_intvl = None
        self.sumry_intvl = None
        self.count_start = None

        self.count_lim_sv = tk.StringVar()
        self.time_start_sv = tk.StringVar()
        self.count_intvl_sv = tk.StringVar()
        self.sumry_intvl_sv = tk.StringVar()
        self.count_start_sv = tk.StringVar()

        # Common data reports var
        self.tt_mean = None
        self.tt_sd = None
        self.tt_lo = None
        self.tt_hi = None
        self.tt_sum = None
        self.time_now = None
        self.count_next = None
        self.count_remain = None

        self.tt_mean_sv = tk.StringVar()
        self.tt_sd_sv = tk.StringVar()
        self.tt_lo_sv = tk.StringVar()
        self.tt_hi_sv = tk.StringVar()
        self.tt_sum_sv = tk.StringVar()
        self.time_now_sv = tk.StringVar()
        self.next_var = tk.StringVar()
        self.count_remain_sv = tk.StringVar()

        # Unique to interval data report var
        self.count_now = None
        self.tic_nnt = None

        self.count_now_sv = tk.StringVar()
        self.tic_nnt_sv = tk.IntVar()

        # Unique to summary data report var
        self.count_uniq = None
        self.count_uniq_sv = tk.StringVar()

        # stubdata is only for testing GUI layout.
        self.set_stubdata()

        # self.set_startdata(self.datadict)
        # TODO: Figure out how to bring in data from count-tasks data_intervals().

        # Set starting data colors (same as config_intvldata) and starting
        #   data labels.
        self.config_startdata()
        self.show_startdata()

        # tkinter's infinite event loop
        # "Always call mainloop as the last logical line of code in your
        # program." per Bryan Oakly:
        # https://stackoverflow.com/questions/29158220/tkinter-understanding-mainloop
        self.mainwin.mainloop()

    def mainwin_cfg(self) -> None:
        """
        Configure colors, key binds & basic behavior of data_intervals Tk window.
        """
        # Needed for data readability in smallest resized dataframe. Depends
        #   on platform; set for Linux with its largest relative font size.
        self.mainwin.minsize(466, 390)

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

        self.mainwin.bind("<Escape>", lambda q: self.quitnow())
        self.mainwin.bind("<Control-q>", lambda q: self.quitnow())
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
        self.dataframe = tk.LabelFrame(borderwidth=3,
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
            tk.Label(text=f'{header}',
                     bg=self.mainwin_bg,
                     fg=self.row_fg
                     ).grid(row=rownum, column=0,
                            padx=(5, 0), sticky=tk.E)

    def mainwin_widgets(self) -> None:
        """
        Layout menus, buttons, separators, row labels in data_intervals Tk window.
        """

        # creating a menu instance
        menu = tk.Menu(self.mainwin)
        self.mainwin.config(menu=menu)

        # Add pull-down menus
        file = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="File", menu=file)
        file.add_command(label="Backup log file", command=self.backup_log)
        file.add_separator()
        file.add_command(label="Quit", command=self.quitnow,
                         accelerator="Ctrl+Q")

        view = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="View", menu=view)
        view.add_command(label="Log file", command=self.show_log,
                         accelerator="Ctrl+L")

        info = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Help", menu=info)
        info.add_command(label="Info", state=tk.DISABLED)
        info.add_command(label="Compliment", command=self.compliment,
                         accelerator="Ctrl+Shift+C")
        info.add_command(label="About", command=self.about)

        # Create button widgets:
        style = ttk.Style()
        style.configure('TButton', background='grey80', anchor='center')
        ttk.Button(text='View log file',
                   command=self.show_log).grid(row=0, column=0,
                                               padx=5, pady=5)
        ttk.Button(text='Recent count',
                   command=self.config_intvldata).grid(row=0, column=1,
                                                       padx=0, pady=5)
        ttk.Button(text='Recent summary',
                   command=self.config_sumrydata).grid(row=0, column=2,
                                                       padx=(0, 25), pady=5)
        ttk.Button(text="Quit",
                   command=self.quitnow).grid(row=12, column=2,
                                              padx=5, sticky=tk.E)
        # Start button used only to test progressbar
        ttk.Button(text="Run test bar",
                   command=self.increment_prog).grid(row=12, column=1,
                                                     padx=5, sticky=tk.E)

        # For colored separators, use ttk.Frame instead of ttk.Separator.
        # Initialize then configure style for separator color.
        # style = ttk.Style()
        style.configure('TFrame', background=self.mainwin_bg)
        sep1 = ttk.Frame(self.mainwin, relief="raised", height=6)
        sep2 = ttk.Frame(self.mainwin, relief="raised", height=6)
        sep1.grid(column=0, row=1, columnspan=5,
                  padx=5, pady=(2, 5), sticky=tk.EW)
        sep2.grid(column=0, row=9, columnspan=5,
                  padx=5, pady=(6, 6), sticky=tk.EW)

    def config_startdata(self) -> None:
        """
        Populate initial data table from count-tasks.

        :return: Starting BOINC data from past hour.
        """
        self.intvl_t[0]     = 'grey90'
        self.intvl_main[0]  = 'gold'
        self.intvl_stat[0]  = 'grey90'
        self.sumry_t[0]     = 'grey60'
        self.sumry_main[0]  = 'grey60'
        self.sumry_stat[0]  = 'grey60'
        self.show_startdata()

    def config_intvldata(self) -> None:
        """
        Switch visual emphasis to interval data; update interval data.

        :return: Highlighted interval data, de-emphasized summary data.
        """
        self.intvl_t[0]     = 'grey90'
        self.intvl_main[0]  = 'gold'
        self.intvl_stat[0]  = 'grey90'
        self.sumry_t[0]     = 'grey60'
        self.sumry_main[0]  = 'grey60'
        self.sumry_stat[0]  = 'grey60'
        self.show_updatedata()
        # ".show" redraws data Labels each time. Necessary to update data?
        # Or use some .configure method to re-color Labels and update data
        # another way?

    def config_sumrydata(self) -> None:
        """
        Switch visual emphasis to summary data; update summary data.

        :return: Highlighted summary data, de-emphasized interval data.
        """
        self.intvl_t[0]     = 'grey60'
        self.intvl_main[0]  = 'grey60'
        self.intvl_stat[0]  = 'grey60'
        self.sumry_t[0]     = 'grey90'
        self.sumry_main[0]  = 'gold'
        self.sumry_stat[0]  = 'grey90'
        self.show_updatedata()

    def set_stubdata(self):
        """
        Test data for GUI table layout.

        :return: Data for assigning and updating dataframe labels.
        """

        # Starting report
        # Stub data strings for testing
        self.count_lim = '1008'
        self.count_lim_sv.set(self.count_lim)
        self.time_start = '2020-Nov-10 10:00:10'
        self.time_start_sv.set(self.time_start)
        self.count_intvl = '60m'
        self.count_intvl_sv.set(self.count_intvl)
        self.sumry_intvl = '1d'
        self.sumry_intvl_sv.set(self.sumry_intvl)
        self.count_start = '24'
        self.count_start_sv.set(self.count_start)

        # Common data reports
        self.tt_mean = '00:25:47'
        self.tt_mean_sv.set(self.tt_mean)
        self.tt_sd = '00:00:26'
        self.tt_sd_sv.set(self.tt_sd)
        self.tt_lo = '00:17:26'
        self.tt_lo_sv.set(self.tt_lo)
        self.tt_hi = '00:25:47'
        self.tt_hi_sv.set(self.tt_hi)
        self.tt_sum = '10:25:47'
        self.tt_sum_sv.set(self.tt_sum)
        self.time_now = '2020-Nov-17 11:14:25'
        self.time_now_sv.set(self.time_now)
        self.count_next = '27m'
        self.next_var.set(self.count_next)
        self.count_remain = '1000'
        self.count_remain_sv.set(self.count_remain)

        # Interval data report
        self.count_now = '21'
        self.count_now_sv.set(self.count_now)
        # self.tic_nnt = 0
        # self.tic_nnt_sv.set(self.tic_nnt)

        # Summary data report
        self.count_uniq = '123'
        self.count_uniq_sv.set(self.count_uniq)

#    TODO: Figure out how to get startdata from count-tasks.
    # Set methods are for data from count-tasks data_intervals().
    def set_startdata(self, **datadict):
        # def set_startdata(self, time_start,
        #                   count_intvl, sumry_intvl,
        #                   count_start,
        #                   tt_lo, tt_hi, tt_sd, tt_sum,
        #                   count_lim):
        """
        Set StringVars with starting data from count-tasks data_intervals().

        :param datadict: Dict of report data vars with matching keywords.
        :type datadict: dict
        :return: Initial textvariables for datatable labels.
        """
        print('this is startdata from gui:', datadict)  # for testing
        self.time_start_sv.set(datadict['time_start'])
        self.count_intvl_sv.set(datadict['count_intvl'])
        self.sumry_intvl_sv.set(datadict['sumry_intvl'])
        self.count_start_sv.set(datadict['count_start'])
        self.tt_hi_sv.set(datadict['tt_hi'])
        self.tt_lo_sv.set(datadict['tt_lo'])
        self.tt_sd_sv.set(datadict['tt_sd'])
        self.tt_sum_sv.set(datadict['tt_sum'])
        # self.time_start_sv.set(time_start)
        # self.count_intvl_sv.set(count_intvl)
        # self.sumry_intvl_sv.set(sumry_intvl)
        # self.count_start_sv.set(count_start)
        # self.tt_hi_sv.set(tt_hi)
        # self.tt_lo_sv.set(tt_lo)
        # self.tt_sd_sv.set(tt_sd)
        # self.tt_sum_sv.set(tt_sum)
        # self.count_lim_sv.set(count_lim)
    #     # self.count_lim_sv.set(datadict.get('count_lim', 'unk key'))
        self.config_startdata()

    def set_intvldata(self, datadict: dict):
        """
        Set StringVars with interval data from count-tasks data_intervals().

        :param datadict: Dict of report data vars with matching keywords.
        :return: Updated interval textvariables for datatable labels.
        """

        self.time_now_sv.set(datadict['time_now'])
        self.count_now_sv.set(datadict['count_now'])
        self.tt_hi_sv.set(datadict['tt_hi'])
        self.tt_lo_sv.set(datadict['tt_lo'])
        self.tt_sd_sv.set(datadict['tt_sd'])
        self.tt_sum_sv.set(datadict['tt_sum'])
        self.count_remain_sv.set(datadict['count_remain'])

        # self.show_updatedata()  # is this needed?
        # mainwin.update()  # is this needed?  Need new values in data labels.

    def set_sumrydata(self, datadict: dict):
        """
        Set StringVars with summary data from count-tasks data_intervals().

        :param datadict: Dict of report data vars with matching keywords.
        :return: Summary textvariables for datatable labels.
        """

        self.time_now_sv.set(datadict['time_now'])
        self.count_uniq_sv.set(datadict['count_uniq'])
        self.tt_hi_sv.set(datadict['tt_hi'])
        self.tt_lo_sv.set(datadict['tt_lo'])
        self.tt_sd_sv.set(datadict['tt_sd'])
        self.tt_sum_sv.set(datadict['tt_sum'])

        # self.show_updatedata()  # is this needed?
        # mainwin.update()  # is this needed?  Need new values in data labels.

    # Methods to define and show data labels.
    def show_startdata(self) -> None:
        """
        Show count-tasks starting data in GUI data table.

        :return: count-tasks datatable
        """

        # Starting datetime of count-tasks; fg is invariant here.
        # Start time label is static; don't need a textvariable.
        tk.Label(self.dataframe, textvariable=self.time_start_sv,
                 # font=('TkTextFont', 10),
                 bg=self.data_bg, fg='grey90'
                 ).grid(row=2, column=1, columnspan=2,
                        padx=10, sticky=tk.EW)

        # Starting count data and times (from past boinc-client hour).
        time_range = self.tt_lo_sv.get() + ' -- ' + self.tt_hi_sv.get()

        tk.Label(self.dataframe, textvariable=self.count_intvl_sv,
                 width=20,  # Longest data cell is time range, 20 char.
                 relief='groove', borderwidth=2,
                 # font=('TkTextFont', 10),
                 bg=self.data_bg, fg=self.intvl_t
                 ).grid(row=3, column=1, padx=10, sticky=tk.EW)
        tk.Label(self.dataframe, textvariable=self.sumry_intvl_sv,
                 width=20,
                 relief='groove', borderwidth=2,
                 # font=('TkTextFont', 10),
                 bg=self.data_bg, fg=self.sumry_t
                 ).grid(row=3, column=2, padx=(0, 10), sticky=tk.EW)
        tk.Label(self.dataframe, textvariable=self.count_now_sv,
                 # font=('TkTextFont', 12),
                 bg=self.data_bg, fg=self.intvl_main
                 ).grid(row=4, column=1, padx=10, sticky=tk.EW)
        tk.Label(self.dataframe, textvariable=self.tt_mean_sv,
                 # font=('TkTextFont', 12),
                 bg=self.data_bg, fg=self.intvl_main
                 ).grid(row=5, column=1, padx=10, sticky=tk.EW)
        tk.Label(self.dataframe, textvariable=self.tt_sd_sv,
                 # font=('TkTextFont', 10),
                 bg=self.data_bg, fg=self.intvl_stat
                 ).grid(row=6, column=1,  padx=10, sticky=tk.EW)
        tk.Label(self.dataframe, text=time_range,
                 # font=('TkTextFont', 10),
                 bg=self.data_bg, fg=self.intvl_stat
                 ).grid(row=7, column=1,  padx=10, sticky=tk.EW)
        tk.Label(self.dataframe, textvariable=self.tt_sum_sv,
                 # font=('TkTextFont', 10),
                 bg=self.data_bg, fg=self.intvl_stat
                 ).grid(row=8, column=1, padx=10, sticky=tk.EW)

        # Previous and until task count times.
        tk.Label(textvariable=self.time_now_sv,
                 bg=self.mainwin_bg, fg=self.row_fg
                 ).grid(row=10, column=1, sticky=tk.W)
        tk.Label(textvariable=self.count_remain_sv,
                 bg=self.mainwin_bg, fg=self.row_fg
                 ).grid(row=11, column=1, sticky=tk.W)
        tk.Label(textvariable=self.next_var,
                 bg=self.mainwin_bg, fg=self.row_fg
                 ).grid(row=12, column=1, sticky=tk.W)

    def show_updatedata(self) -> None:
        """
        Place count-tasks data in GUI data table.

        :return: count-tasks datatable.
        """
        # show_updatedata includes the interval and summary data columns.
        # Make a separate show_sumrydata() method?
        # Both reports are triggered by a common count-tasks interval event.

        # Count and summary interval times
        tk.Label(self.dataframe, textvariable=self.count_intvl_sv,
                 width=20,  # Longest data cell is time range, 20 char.
                 relief='groove', borderwidth=2,
                 # font=('TkTextFont', 10),
                 bg=self.data_bg, fg=self.intvl_t
                 ).grid(row=3, column=1, padx=10, sticky=tk.EW)
        tk.Label(self.dataframe, textvariable=self.sumry_intvl_sv,
                 width=20,
                 relief='groove', borderwidth=2,
                 # font=('TkTextFont', 10),
                 bg=self.data_bg, fg=self.sumry_t
                 ).grid(row=3, column=2, padx=(0, 10), sticky=tk.EW)

        # Interval data, column1
        range_cat = self.tt_lo_sv.get() + ' -- ' + self.tt_hi_sv.get()

        tk.Label(self.dataframe, textvariable=self.count_now_sv,
                 # font=('TkTextFont', 12),
                 bg=self.data_bg, fg=self.intvl_main
                 ).grid(row=4, column=1, padx=10, sticky=tk.EW)
        tk.Label(self.dataframe, textvariable=self.tt_mean_sv,
                 # font=('TkTextFont', 12),
                 bg=self.data_bg, fg=self.intvl_main
                 ).grid(row=5, column=1, padx=10, sticky=tk.EW)
        tk.Label(self.dataframe, textvariable=self.tt_sd_sv,
                 # font=('TkTextFont', 10),
                 bg=self.data_bg, fg=self.intvl_stat
                 ).grid(row=6, column=1,  padx=10, sticky=tk.EW)
        tk.Label(self.dataframe, text=range_cat,
                 # font=('TkTextFont', 10),
                 bg=self.data_bg, fg=self.intvl_stat
                 ).grid(row=7, column=1,  padx=10, sticky=tk.EW)
        tk.Label(self.dataframe, textvariable=self.tt_sum_sv,
                 # font=('TkTextFont', 10),
                 bg=self.data_bg, fg=self.intvl_stat
                 ).grid(row=8, column=1,
                        padx=10, sticky=tk.EW)

        # Summary data, column2
        tk.Label(self.dataframe, textvariable=self.count_uniq_sv,
                 # font=('TkTextFont', 12),
                 bg=self.data_bg, fg=self.sumry_main
                 ).grid(row=4, column=2, padx=(0, 10), sticky=tk.EW)
        tk.Label(self.dataframe, textvariable=self.tt_mean_sv,
                 # font=('TkTextFont', 12),
                 bg=self.data_bg, fg=self.sumry_main
                 ).grid(row=5, column=2, padx=(0, 10), sticky=tk.EW)
        tk.Label(self.dataframe, textvariable=self.tt_sd_sv,
                 # font=('TkTextFont', 10),
                 bg=self.data_bg, fg=self.sumry_stat
                 ).grid(row=6, column=2, padx=(0, 10), sticky=tk.EW)
        tk.Label(self.dataframe, text=range_cat,
                 # font=('TkTextFont', 10),
                 bg=self.data_bg, fg=self.sumry_stat
                 ).grid(row=7, column=2, padx=(0, 10), sticky=tk.EW)
        tk.Label(self.dataframe, textvariable=self.tt_sum_sv,
                 # font=('TkTextFont', 10),
                 bg=self.data_bg, fg=self.sumry_stat
                 ).grid(row=8, column=2, padx=(0, 10), sticky=tk.EW)

        # Previous and until task count times.
        tk.Label(textvariable=self.time_now_sv,
                 bg=self.mainwin_bg, fg=self.row_fg
                 ).grid(row=10, column=1, sticky=tk.W)
        tk.Label(textvariable=self.count_remain_sv,
                 bg=self.mainwin_bg, fg=self.row_fg
                 ).grid(row=11, column=1, sticky=tk.W)
        tk.Label(textvariable=self.next_var,
                 bg=self.mainwin_bg, fg=self.row_fg
                 ).grid(row=12, column=1, sticky=tk.W)

    # Methods for menu items and keybinds.
    def quitnow(self) -> None:
        """Safe and informative exit from the program.
        """
        print('\n  --- User has quit the count-tasks GUI. ---\n')
        self.mainwin.destroy()

    @staticmethod
    def about() -> None:
        """
        Basic information for count-tasks; called from the Help menu.

        :return: Information window.
        """
        # msg separators use em dashes.
        msg = ("""
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

        msg_lines = msg.count('\n')
        aboutwin = tk.Toplevel()
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
        abouttxt = tk.Text(aboutwin, width=72, height=msg_lines+2,
                           background=bkg, foreground='grey98',
                           relief='groove', borderwidth=5, padx=5)
        abouttxt.insert('1.0', msg + PROGRAM_VER)
        # Center text preceding the Author, etc. details.
        abouttxt.tag_add('text1', '1.0', float(msg_lines-5))
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
        except FileNotFoundError as fnferr:
            msg = ('The file count-tasks_log.txt is not in the'
                   ' CountBOINCtasks-master folder.\n'
                   'Has the file been created with the --log command line option?')
            print(f'{msg}\n{fnferr}')
            logwin = tk.Toplevel()
            logwin.attributes('-topmost', 1)  # for Windows, needed?
            logwin.title('View log error')
            logtext = tk.Text(logwin, width=75, height=4, bg='grey85',
                              fg='red', relief='raised', padx=5)
            logtext.insert(tk.INSERT, msg)
            logtext.grid(row=0, column=0, sticky=tk.NSEW)
            logtext.focus_set()

    @staticmethod
    def backup_log() -> None:
        """
        Copy the log file to the home folder; called from the File menu.

        :return: A new or overwritten backup file.
        """

        destination = Path.home() / BKUPFILE
        if Path.is_file(LOGPATH) is True:
            shutil.copyfile(LOGPATH, destination)
            msg = 'Log file has been copied to ' + str(destination)
            # Main window alert; needed along with notification in new window?
            # text = tk.Label(text=msg, font=('default', 10),
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
            logtext.insert(tk.INSERT, msg)
            logtext.grid(row=0, column=0, sticky=tk.NSEW)
            logtext.focus_set()
        else:
            msg = (f'The file {LOGPATH} cannot be archived because it\n'
                   '  is not in the CountBOINCtasks-master folder.\n'
                   'Has the file been created with the --log command line option?\n'
                   'Or perhaps it has been moved?')
            print(msg)
            # Need a persistent window alert in addition to a terminal alert.
            logwin = tk.Toplevel()
            logwin.attributes('-topmost', 1)
            logwin.title('Archive log error')
            logtext = tk.Text(logwin, width=62, height=4,
                              fg='red', bg='grey85',
                              relief='raised', padx=5)
            logtext.insert(tk.INSERT, msg)
            logtext.grid(row=0, column=0, sticky=tk.NSEW)
            logtext.focus_set()

    def compliment(self) -> None:
        """
         A silly diversion; used with the 'compliment' menu item.

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
        text = tk.Label(text=txt,
                        # font=('default', 10),
                        foreground='DodgerBlue4',
                        background='gold2',
                        relief='flat',
                        border=0)
        text.grid(row=2, column=1, columnspan=2,
                  padx=(15, 20),  sticky=tk.EW)
        # To fit well, pady ^here must match pady of the same data label row.
        self.mainwin.after(2468, text.destroy)

    # Optional feature:
    # TODO: Integrate Progressbar widget with count-tasks intvl_timer.
    progress = ttk.Progressbar(orient=tk.HORIZONTAL, length=100,
                               mode='determinate')
    progress.grid(row=13, column=0, columnspan=3,
                  padx=5, pady=5, sticky=tk.EW)

    def increment_prog(self) -> None:
        """
        Used to test drive the Progressbar.

        :return: timing of progress bar.
        """
    # https://stackoverflow.com/questions/33768577/tkinter-gui-with-progress-bar
    # Read answer to structure bar with threading, but threading may not be good.
        # Note that this prevents all other module actions while running
        for i in range(100):
            CountGui.progress["value"] = i + 1
            self.mainwin.update()
            time.sleep(0.1)
        CountGui.progress["value"] = 0  # Reset bar


CountGui()

# Use this once integrate this module with count-tasks data_intervals().
# def about() -> None:
#     """
#     Print details about_gui this module.
#     """
#     print(__doc__)
#     print('Author: ', __author__)
#     print('Copyright: ', __copyright__)
#     print('Credits: ', *[f'\n      {item}' for item in __credits__])
#     print('License: ', __license__)
#     print('Version: ', __version__)
#     print('Maintainer: ', __maintainer__)
#     print('Status: ', __status__)
#     sys.exit(0)
#
#
# if __name__ == '__main__':
#     about()