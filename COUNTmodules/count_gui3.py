#!/usr/bin/env python3
"""
A test module to construct tkinter GUI for displaying count-tasks data.

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

# import os
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

# BC = boinc_command.BoincCommand()
# Assume log file is in the CountBOINCtasks-master folder.
# Not sure what determines which relative path. Depends on copying the mod.
LOGPATH = Path('../count-tasks_log.txt')
# LOGPATH = Path('count-tasks_log.txt')
BKUPFILE = "count-tasks_log(copy).txt"
SCRIPT_VER = '0.5'

# __author__      = 'cecht, BOINC ID: 990821'
# __copyright__   = 'Copyright (C) 2020 C. Echt'
# __credits__     = ['Inspired by rickslab-gpu-utils',
#                    'Keith Myers - Testing, debug']
# __license__     = 'GNU General Public License'
# __program_name__ = 'count-tasks.py'
# __version__     = script_ver
# __maintainer__  = 'cecht'
# __docformat__   = 'reStructuredText'
# __status__      = 'Development Status :: 4 - Beta'

# https://python.readthedocs.io/en/stable/library/tk.html
# Original code source:
# https://pythonprogramming.net/python-3-tkinter-basics-tutorial/

mainwin = tk.Tk()
mainwin.title("count-tasks")


class GuiSetup:
    """
    A GUI window to display data from count-tasks.
    """

    def __init__(self, **kwargs):

        self.dataframe = None

        self.row_fg = None
        self.data_bg = None
        self.mainwin_bg = None

        self.mainwin_cfg()
        self.mainwin_widgets()

        # mainwin.mainloop() is handled in DataGui __init__.

    def mainwin_cfg(self) -> None:
        """
        Configure colors, bindings, and basic behavior of main window.
        """
        # Set colors for row labels and data display.
        # http://www.science.smith.edu/dftwiki/index.php/Color_Charts_for_TKinter
        self.row_fg = 'LightCyan2'  # foreground for row labels
        self.data_bg = 'grey40'  # background for data labels and frame
        # window background & used for some labels.
        self.mainwin_bg = 'SkyBlue4'
        mainwin.configure(bg=self.mainwin_bg)

        # Use of theme overrides most tk font and border options.
        # Controls entire window theme. Opt: alt, clam, default, aqua(MacOS)
        # ttk.Style().theme_use('classic')

        # mainwin.bind("<Escape>", lambda q: mainwin.destroy())
        mainwin.bind("<Escape>", lambda q: quitnow())
        mainwin.bind("<Control-q>", lambda q: quitnow())
        mainwin.bind("<Control-C>", lambda q: compliment())
        mainwin.bind("<Control-l>", lambda q: show_log())

        # Make data rows and columns stretch with window drag size.
        rows2config = (2, 3, 4, 5, 6, 7, 8, 10, 11, 12)
        for r in rows2config:
            mainwin.rowconfigure(r, weight=1)

        mainwin.columnconfigure(1, weight=1)
        mainwin.columnconfigure(2, weight=1)
        # Needed for data readability in smallest resized dataframe.
        mainwin.minsize(444, 370)

        # Set up frame to display data. Putting frame here instead of in
        # mainwin_widgets gives proper alignment of row headers and data.
        self.dataframe = tk.LabelFrame(borderwidth=2, relief='sunken',
                                       background=self.data_bg)
        self.dataframe.grid(row=2, column=1, rowspan=7, columnspan=2,
                            padx=5, sticky=tk.NSEW)
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
                    'Last count was':     10,
                    '# counts remaining:': 11,
                    'Next count in':      12
                     }
        for key, value in row_header.items():
            tk.Label(text=f'{key}',
                     bg=self.mainwin_bg,
                     fg=self.row_fg
                     ).grid(row=value, column=0,
                            padx=(5, 0), pady=(0, 0), sticky=tk.E)

    def mainwin_widgets(self) -> None:
        """
        Layout menus, buttons, separators, row labels in main window.
        """

        # creating a menu instance
        menu = tk.Menu(mainwin)
        mainwin.config(menu=menu)

        # Add pull-down menus
        file = tk.Menu(menu, tearoff=0)

        menu.add_cascade(label="File", menu=file)
        file.add_command(label="Archive log", command=archive_log)
        file.add_separator()
        file.add_command(label="Quit", command=quitnow, accelerator="Ctrl+Q")

        view = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="View", menu=view)
        view.add_command(label="Log file", command=show_log,
                         accelerator="Ctrl+L")

        info = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Help", menu=info)
        info.add_command(label="Info", state=tk.DISABLED)
        info.add_command(label="Compliment", command=compliment,
                         accelerator="Ctrl+Shift+C")
        info.add_command(label="About", command=about)
        # Create button widgets:
        tk.Button(text='View log file',
                  command=show_log).grid(row=0, column=0,
                                         padx=5, pady=5)

        # Interval and Summary configuration buttons in GuiData

        # Start button used only to test progressbar
        tk.Button(text="Start bar", font=('default', 8),
                  command=increment_prog).grid(row=12, column=1,
                                               padx=5, sticky=tk.E)

        tk.Button(text="Quit", font=('default', 10),
                  command=quitnow).grid(row=12, column=2,
                                        padx=5, sticky=tk.E)

        # For colored separators, use ttk.Frame instead of ttk.Separator.
        # Initialize then configure style for separator color.
        style = ttk.Style()
        style.configure('TFrame', background=self.mainwin_bg)
        sep1 = ttk.Frame(mainwin, relief="raised", height=5)
        sep2 = ttk.Frame(mainwin, relief="raised", height=5)
        # sep1, Use no top pady; button widgets will set padding.
        sep1.grid(column=0, row=1, columnspan=5,
                  padx=5, pady=(2, 5), sticky=tk.EW)
        sep2.grid(column=0, row=9, columnspan=5,
                  padx=5, pady=(6, 4), sticky=tk.EW)


class GuiData(GuiSetup):
    """
    Populate gui window with count_tasks data.
    """

    def __init__(self, **kwargs):
        super().__init__()
        # self.datadict = kwargs

        # Mutable color variables used for emphasizing different data
        # categories via buttons.
        self.intvl_t    = ['']
        self.intvl_main = ['']
        self.intvl_stat = ['']
        self.sumry_t    = ['']
        self.sumry_main = ['']
        self.sumry_stat = ['']

        # Starting data report
        # Vars names are used only in stubdata().
        # _sv can be refactored w/o suffix and assigned as StringVar
        # objects in a for loop with .append from a list or dictionary?
        self.count_lim = ''
        self.count_lim_sv = tk.StringVar()
        self.time_start = ''
        self.time_start_sv = tk.StringVar()
        self.count_intvl = ''
        self.count_intvl_sv = tk.StringVar()
        self.sumry_intvl = ''
        self.sumry_intvl_sv = tk.StringVar()
        self.count_start = ''
        self.count_start_sv = tk.StringVar()

        # Common data reports
        self.tt_mean = ''
        self.tt_mean_sv = tk.StringVar()
        self.tt_sd = ''
        self.tt_sd_sv = tk.StringVar()
        self.tt_lo = ''
        self.tt_lo_sv = tk.StringVar()
        self.tt_hi = ''
        self.tt_hi_sv = tk.StringVar()
        self.tt_sum = ''
        self.tt_sum_sv = tk.StringVar()
        self.time_now = ''
        self.time_now_sv = tk.StringVar()
        self.count_next = ''
        self.next_var = tk.StringVar()
        self.count_remain = ''
        self.count_remain_sv = tk.StringVar()

        # Unique to interval data report
        self.count_now = ''
        self.count_now_sv = tk.StringVar()

        # Unique to summary data report
        self. count_uniq = ''
        self.count_uniq_sv = tk.StringVar()

        tk.Button(text='Recent count',
                  command=self.config_intvldata).grid(row=0, column=1,
                                                      padx=2, pady=5)
        tk.Button(text='Recent summary',
                  command=self.config_sumrydata).grid(row=0, column=2,
                                                      padx=2, pady=5)

        self.set_stubdata()
        # self.set_startdata()

        # Set starting data colors (same as for intvl_config.)
        # Populate start_data labels in main dataframe table
        self.config_startdata()

        # Call mainloop when ready to have program run. It runs loop until
        # window is closed. Any of these work.
        # self.dataframe.mainloop()
        # self.master.mainloop()
        mainwin.mainloop()

    def config_startdata(self) -> None:
        """
        Populates initial data table from count-tasks.

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
        # This redraws data Labels each time. Necessary to update data?
        # Or use some .configure method to re-color Labels and update data
        # another way?

    def config_sumrydata(self):
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

    def set_startdata(self, **startdata: dict):
        """
        Set StringVars with starting data from count-tasks main().

        :param startdata: Dict of main() report data var with matching
        keywords.
        :return: Initial textvariables for datatable labels.
        """

        self.time_start_sv.set(startdata['time_start'])
        self.count_intvl_sv.set(startdata['count_intvl'])
        self.sumry_intvl_sv.set(startdata['sumry_intvl'])
        self.count_start_sv.set(startdata['count_start'])
        self.tt_hi_sv.set(startdata['tt_hi'])
        self.tt_lo_sv.set(startdata['tt_lo'])
        self.tt_sd_sv.set(startdata['tt_sd'])
        self.tt_sum_sv.set(startdata['tt_sum'])
        self.count_lim_sv.set(startdata['count_lim'])
    #     # self.count_lim_sv.set(kwargs.get('count_lim', 'unk key'))
    #     # return anything?

    def set_intvldata(self, **intvldata: dict):
        """
        Set StringVars with interval data from count-tasks main().

        :param intvldata: Dict of main() report data var with matching
        keywords.
        :return: Updated interval textvariables for datatable labels.
        """

        self.time_now_sv.set(intvldata['time_now'])
        self.count_now_sv.set(intvldata['count_now'])
        self.tt_hi_sv.set(intvldata['tt_hi'])
        self.tt_lo_sv.set(intvldata['tt_lo'])
        self.tt_sd_sv.set(intvldata['tt_sd'])
        self.tt_sum_sv.set(intvldata['tt_sum'])
        self.count_remain_sv.set(intvldata['count_remain'])

        # self.show_updatedata()  # is this needed?
        # mainwin.update()  # is this needed?  Need new values in data labels.

    def set_sumrydata(self, **sumrydata: dict):
        """
        Set StringVars with summary data from count-tasks main().

        :param sumrydata: Dict of main() report data var with matching
        keywords.
        :return: Summary textvariables for datatable labels.
        """

        self.time_now_sv.set(sumrydata['time_now'])
        self.count_uniq_sv.set(sumrydata['count_uniq'])
        self.tt_hi_sv.set(sumrydata['tt_hi'])
        self.tt_lo_sv.set(sumrydata['tt_lo'])
        self.tt_sd_sv.set(sumrydata['tt_sd'])
        self.tt_sum_sv.set(sumrydata['tt_sum'])

        # self.show_updatedata()  # is this needed?
        # mainwin.update()  # is this needed?  Need new values in data labels.

    def show_startdata(self) -> None:
        """
        Show count-tasks starting data in GUI data table.

        :return: count-tasks datatable
        """

        # TODO: ADD row-label for max. count cycles (count_lim) and consider
        #  another for cycles remaining before program quits (in last row?);
        #  place on a new row with report on tic_nnt, no tasks reported.

        # Starting datetime of count-tasks; fg is invariant here.
        tk.Label(self.dataframe, textvariable=self.time_start_sv,
                 bg=self.data_bg, fg='grey90'
                 ).grid(row=2, column=1, columnspan=2,
                        padx=15, pady=(0, 3), sticky=tk.EW)

        # Starting count data and times (from past boinc-client hour).
        range_cat = self.tt_lo_sv.get() + ' -- ' + self.tt_hi_sv.get()

        # TODO: Create labels in a loop iterating over a list or dict?
        tk.Label(self.dataframe, textvariable=self.count_intvl_sv,
                 width=20,  # Longest data cell is time range, 20 char.
                 relief='groove', borderwidth=2, font=('TkTextFont', 10),
                 bg=self.data_bg, fg=self.intvl_t
                 ).grid(row=3, column=1, padx=15, sticky=tk.EW)
        tk.Label(self.dataframe, textvariable=self.sumry_intvl_sv,
                 width=20,
                 relief='groove', borderwidth=2, font=('TkTextFont', 10),
                 bg=self.data_bg, fg=self.sumry_t
                 ).grid(row=3, column=2, padx=(0, 15), sticky=tk.EW)
        tk.Label(self.dataframe, textvariable=self.count_now_sv,
                 bg=self.data_bg, fg=self.intvl_main
                 ).grid(row=4, column=1, padx=15, sticky=tk.EW)
        tk.Label(self.dataframe, textvariable=self.tt_mean_sv,
                 bg=self.data_bg, fg=self.intvl_main
                 ).grid(row=5, column=1, padx=15, sticky=tk.EW)
        tk.Label(self.dataframe, textvariable=self.tt_sd_sv,
                 bg=self.data_bg, fg=self.intvl_stat
                 ).grid(row=6, column=1,  padx=15, sticky=tk.EW)
        tk.Label(self.dataframe, text=range_cat,
                 bg=self.data_bg, fg=self.intvl_stat
                 ).grid(row=7, column=1,  padx=15, sticky=tk.EW)
        tk.Label(self.dataframe, textvariable=self.tt_sum_sv,
                 bg=self.data_bg, fg=self.intvl_stat
                 ).grid(row=8, column=1,  padx=15, sticky=tk.EW)

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

    # This method includes the interval and summary data columns.
    # Make a separate show_sumrydata() method?
    def show_updatedata(self) -> None:
        """
        Place count-tasks data in GUI data table.

        :return: count-tasks datatable.
        """

        # Count and summary interval times
        tk.Label(self.dataframe, textvariable=self.count_intvl_sv,
                 width=20,  # Longest data cell is time range, 20 char.
                 relief='groove', borderwidth=2, font=('TkTextFont', 10),
                 bg=self.data_bg, fg=self.intvl_t
                 ).grid(row=3, column=1, padx=15, sticky=tk.EW)
        tk.Label(self.dataframe, textvariable=self.sumry_intvl_sv,
                 width=20,
                 relief='groove', borderwidth=2, font=('TkTextFont', 10),
                 bg=self.data_bg, fg=self.sumry_t
                 ).grid(row=3, column=2, padx=(0, 15), sticky=tk.EW)

        # Interval data, column1
        range_cat = self.tt_lo_sv.get() + ' -- ' + self.tt_hi_sv.get()

        tk.Label(self.dataframe, textvariable=self.count_now_sv,
                 bg=self.data_bg, fg=self.intvl_main
                 ).grid(row=4, column=1, padx=15, sticky=tk.EW)
        tk.Label(self.dataframe, textvariable=self.tt_mean_sv,
                 bg=self.data_bg, fg=self.intvl_main
                 ).grid(row=5, column=1, padx=15, sticky=tk.EW)
        tk.Label(self.dataframe, textvariable=self.tt_sd_sv,
                 bg=self.data_bg, fg=self.intvl_stat
                 ).grid(row=6, column=1,  padx=15, sticky=tk.EW)
        tk.Label(self.dataframe, text=range_cat,
                 bg=self.data_bg, fg=self.intvl_stat
                 ).grid(row=7, column=1,  padx=15, sticky=tk.EW)
        tk.Label(self.dataframe, textvariable=self.tt_sum_sv,
                 bg=self.data_bg, fg=self.intvl_stat
                 ).grid(row=8, column=1,  padx=15, sticky=tk.EW)

        # Summary data, column2
        tk.Label(self.dataframe, textvariable=self.count_uniq_sv,
                 bg=self.data_bg, fg=self.sumry_main
                 ).grid(row=4, column=2, padx=(0, 10), sticky=tk.EW)
        tk.Label(self.dataframe, textvariable=self.tt_mean_sv,
                 bg=self.data_bg, fg=self.sumry_main
                 ).grid(row=5, column=2, padx=(0, 10), sticky=tk.EW)
        tk.Label(self.dataframe, textvariable=self.tt_sd_sv,
                 bg=self.data_bg, fg=self.sumry_stat
                 ).grid(row=6, column=2,  padx=(0, 10), sticky=tk.EW)
        tk.Label(self.dataframe, text=range_cat,
                 bg=self.data_bg, fg=self.sumry_stat
                 ).grid(row=7, column=2,  padx=(0, 10), sticky=tk.EW)
        tk.Label(self.dataframe, textvariable=self.tt_sum_sv,
                 bg=self.data_bg, fg=self.sumry_stat
                 ).grid(row=8, column=2,  padx=(0, 10), sticky=tk.EW)

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


def quitnow() -> None:
    """Safe and informative exit from the program.
    """
    print('\n  --- User has quit the count-tasks GUI. ---\n')
    mainwin.destroy()


def about() -> None:
    """
    Basic information for count-tasks. Called from Help menu.

    :return: Information window.
    """

    msg = (
        """This program, count-tasks.py, will provide at regular
intervals counts and time statistics of tasks that have
been reported to BOINC servers.

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

            Author:     cecht, BOINC ID: 990821
            Copyright:  Copyright (C) 2020 C. Echt
            Credits:    Inspired by rickslab-gpu-utils,
                        Keith Myers - Testing, debug
            Development Status :: 4 - Beta
            Version: """
    )

    aboutwin = tk.Toplevel()
    aboutwin.title('About count-tasks')
    # aboutimg = tk.PhotoImage(file='../about.png')  # or 'about.png'
    # aboutimg.image = aboutimg  # Need to anchor the image for it to display.
    # tk.Label(aboutwin, image=aboutimg).grid(row=0, column=0, padx=5, pady=5)
    abouttxt = tk.Text(aboutwin, width=72, height=25,
                       background='SkyBlue4', foreground='LightCyan2',
                       relief='raised', padx=5)
    abouttxt.insert('1.0', msg + SCRIPT_VER)
    # Lines 1-18 include only the GNU license boilerplate.
    abouttxt.tag_add('all', '1.0', '18.0')
    abouttxt.tag_configure('all', justify='center')
    abouttxt.pack()


def show_log() -> None:
    """
    Create a separate window to view the log file.

    :return: Read-only log file as scrolled text.
    """

    try:
        with open(LOGPATH, 'r') as log:
            logwin = tk.Toplevel(mainwin)
            logwin.attributes('-topmost', 1)  # for Windows, needed?
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
        logwin = tk.Toplevel(mainwin)
        logwin.attributes('-topmost', 1)  # for Windows, needed?
        logwin.title('View log error')
        logtext = tk.Text(logwin, width=75, height=4, bg='grey85',
                          fg='red', relief='raised', padx=5)
        logtext.insert(tk.INSERT, msg)
        logtext.grid(row=0, column=0, sticky=tk.NSEW)
        logtext.focus_set()


def archive_log() -> None:
    """
    Copy the log file to the home folder. Is called from the File menu.

    :return: A new or overwritten backup file.
    """

    destination = Path.home() / BKUPFILE
    if Path.is_file(LOGPATH) is True:
        shutil.copyfile(LOGPATH, destination)
        msg = 'Log file has been copied to ' + str(destination)
        text = tk.Label(text=msg, font=('default', 10),
                        foreground='DodgerBlue4', background='gold2',
                        relief='flat')
        text.grid(row=9, column=0, columnspan=3,
                  padx=5, pady=6,
                  sticky=tk.EW)
        mainwin.after(5000, text.destroy)
        logwin = tk.Toplevel(mainwin)
        logwin.attributes('-topmost', 1)  # for Windows, needed?
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
        logwin = tk.Toplevel(mainwin)
        logwin.attributes('-topmost', 1)  # for Windows, needed?
        logwin.title('Archive log error')
        logtext = tk.Text(logwin, width=62, height=4,
                          fg='red', bg='grey85',
                          relief='raised', padx=5)
        logtext.insert(tk.INSERT, msg)
        logtext.grid(row=0, column=0, sticky=tk.NSEW)
        logtext.focus_set()


def compliment() -> None:
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
                    font=('default', 10),
                    foreground='DodgerBlue4',
                    background='gold2',
                    relief='flat',
                    border=0)
    text.grid(row=2, column=1, columnspan=2,
              padx=(10, 13), pady=(3, 0), sticky=tk.EW)
    # To fit well, pady ^here must match pady of the data label row.
    mainwin.after(2468, text.destroy)


# TODO: Integrate Progressbar widget with count-tasks sleep_timer.
progress = ttk.Progressbar(orient=tk.HORIZONTAL, length=100,
                           mode='determinate')
progress.grid(row=13, column=0, columnspan=3,
              padx=5, pady=6, sticky=tk.EW)


def increment_prog(incr=100) -> None:
    """
    Used to test drive the Progressbar.

    :param incr: should equal ttk.Progressbar length.
    :return: timing of progress bar.
    """
# https://stackoverflow.com/questions/33768577/tkinter-gui-with-progress-bar
# Read answer to structure bar with threading, but threading may not be good.
    # Note that this prevents all other module actions while running
    for i in range(incr):
        progress["value"] = i + 1
        mainwin.update()
        time.sleep(0.1)
    progress["value"] = 0  # Reset bar


# size = mainwin.grid_size()
# print(size)

GuiSetup()
GuiData()

# Use this once integrate this module with count-tasks main().
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
