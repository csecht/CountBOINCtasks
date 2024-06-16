#!/usr/bin/env python3
"""
General utility functions in gcount-tasks.
Class: Tooltip - Bind mouse hover events to create a tooltip.
Functions:
    check_platform
    run_checks
    manage_args
    use_app_icon
    handle_windows_keyboard_interrupt
    handle_windows_unexpected_error
    handle_nix_exit
    handle_exception
    Tooltip.cancel_wait
    Tooltip.on_enter
    Tooltip.on_leave
    Tooltip.close_now
    Tooltip.tip_pos_calculator
    Tooltip.show_tt
    beep
    enter_only_digits
    position_wrt_window
    about_text
    quit_gui
    exit_text
    verify
"""
# Copyright (C) 2021-2024 C. Echt under GNU General Public License'

# Standard library imports:
import argparse
import logging
import platform
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from time import sleep

if sys.platform[:3] == 'win':
    import winsound

# Third party imports:
import matplotlib.pyplot

# Local program imports:
from __main__ import __doc__
import count_modules as cmod
from count_modules import (boinc_commands,
                           config_constants as const,
                           files,
                           instances,
                           vcheck,
                           )
from count_modules.logs import Logs

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)

MY_OS = sys.platform[:3]


def check_platform():
    if MY_OS not in 'lin, win, dar':
        print(f'Platform <{sys.platform}> is not supported.\n'
              'Windows, Linux, and MacOS (darwin) are supported.')
        sys.exit(1)

    # Need to account for scaling in different Windows releases.
    if MY_OS == 'win':
        from ctypes import windll

        if platform.release() < '10':
            windll.user32.SetProcessDPIAware()
        else:
            windll.shcore.SetProcessDpiAwareness(1)

def run_checks():
    """Program will exit if checks fail"""
    check_platform()
    vcheck.minversion('3.6')
    manage_args()
    boinc_commands.set_boincpath()
    boinc_commands.check_boinc()


def about_text() -> str:
    """
    Informational text for --about execution argument and GUI About call.
    """
    creds = ''.join([f"\n     {item}" for item in cmod.__credits__])
    return (f'{__doc__}\n'
            f'{"Author:".ljust(13)}{cmod.__author__}\n'
            f'{"Credits:"}{creds}\n'
            f'{"Program:".ljust(13)}{instances.program_name()}\n'
            f'{"Version:".ljust(13)}{cmod.__version__}\n'
            f'{"Dev. Env.:".ljust(13)}{cmod.__dev_environment__}\n'
            f'{"URL:".ljust(13)}{cmod.__project_url__}\n'
            f'{"Status:".ljust(13)}{cmod.__status__}\n\n'
            f'{cmod.__copyright__}'
            f'{cmod.LICENSE}\n'
            )
    # To direct print credits from a list:
    #   print(f'{"Credits:".ljust(13)}', *[f"\n      {item}" for item in cmod.__credits__])


def manage_args() -> None:
    """Allow handling of common command line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--about',
                        help='Provides description, version, GNU license',
                        action='store_true',
                        default=False)
    args = parser.parse_args()

    if args.about:
        print('====================== ABOUT START ====================')
        print(about_text())
        print('====================== ABOUT END ====================')

        sys.exit(0)


def use_app_icon(mainloop: tk.Tk) -> None:
    """
    Use custom image to replace blank tk default desktop icon.
    Set correct path to the local 'images' directory and icon file.
    """
    try:
        app_icon = tk.PhotoImage(file=files.valid_path_to('images/count_icon_512.png'))
        mainloop.iconphoto(True, app_icon)
    except tk.TclError:
        print('Cannot display program icon, so it will be left blank or tk default.')


def handle_windows_keyboard_interrupt(sentinel_name) -> None:
    msg = (f"\n{datetime.now().strftime(const.LONG_FMT)};"
           " *** User quit the program from Terminal ***\n"
           f"This instance's temporary file {sentinel_name} has been deleted.\n")
    print(msg)
    logging.info(msg=msg)


def handle_windows_unexpected_error(err_msg, sentinel_name) -> None:
    msg = (f'\n{datetime.now().strftime(const.LONG_FMT)};'
           f'An unexpected error: {err_msg}\n'
           f'This instance\'s temporary file {sentinel_name} has been deleted.\n')
    print(msg)
    logging.info(msg=msg)


def handle_nix_exit() -> None:
    _msg = (f'\n{datetime.now().strftime(const.LONG_FMT)};'
            ' *** User quit the program from Terminal ***')
    print(_msg)
    logging.info(msg=_msg)


def handle_exception(exc_type, exc_value, exc_traceback) -> None:
    """
    Changes an unhandled exception to go to stdout rather than
    stderr. Ignores KeyboardInterrupt so a console program can exit
    with Ctrl + C. Relies entirely on python's logging module for
    formatting the exception. Sources:
    https://stackoverflow.com/questions/6234405/
    logging-uncaught-exceptions-in-python/16993115#16993115
    https://stackoverflow.com/questions/43941276/
    python-tkinter-and-imported-classes-logging-uncaught-exceptions/
    44004413#44004413

    Usage: in mainloop,
     - sys.excepthook = utils.handle_exception
     - app.report_callback_exception = utils.handle_exception

    Args:
        exc_type: The type of the BaseException class.
        exc_value: The value of the BaseException instance.
        exc_traceback: The traceback object.

    Returns: None

    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("Uncaught exception:",
                 exc_info=(exc_type, exc_value, exc_traceback))


class Tooltip:
    """
    Bind mouse hover events to create a Toplevel tooltip with the given
    text for the given widget.

    USAGE: Tooltip(widget, text, state, wait_time, wrap_length)
        widget: tk.widget for which the tootltip is to appear.
        text: the widget's tip; use '' for *state* of 'disabled'.
        state: 'normal' (default) or 'disabled'.
        wait_time (ms): delay of tip appearance (default is 600),
        wrap_length (pixels): of tip window width (default is 250).

        Create a standard tooltip: utils.Tooltip(mywidget, mytext)
        Deactivate: utils.Tooltip(mywidget, '', 'disabled')
        Reactivate with longer wait time and wider wrap length:
          utils.Tooltip(mywidget, mytext, 'normal', 1000, 400)

    see:
    http://stackoverflow.com/questions/3221956/
           what-is-the-simplest-way-to-make-tooltips-
           in-tkinter/36221216#36221216
    http://www.daniweb.com/programming/software-development/
           code/484591/a-tooltip-class-for-tkinter
    - Originally written by vegaseat on 2014.09.09.
    - Modified to include a delay time by Victor Zaccardo on 2016.03.25.
    - Modified
        - to correct extreme right and extreme bottom behavior,
        - to stay inside the screen whenever the tooltip might go out on
          the top but still the screen is higher than the tooltip,
        - to use the more flexible mouse positioning,
        - to add customizable background color, padding, wait_time and
          wrap_len on creation
      by Alberto Vassena on 2016.11.05.
      Tested on Ubuntu 16.04/16.10, running Python 3.5.2

    - Customized for GitHub CountBOINCtasks Project
        by Craig Echt, 12 January 2022.
        Modified to work on multiple platforms and to change state.
        Tested on Linux Ubuntu 20.04, Windows 10, macOS 10.13,
        running Python 3.8 - 3.9
    """

    def __init__(self,
                 widget: tk,
                 tt_text: str,
                 state='normal',
                 wait_time=600,
                 wrap_len=250):

        # wait_time is milliseconds, wrap_len is pixels: as integers.
        self.widget = widget
        self.tt_text = tt_text
        self.wait_time = wait_time
        self.wrap_len = wrap_len

        if state == 'disabled':
            self.widget.bind("<Enter>", lambda _: None)
            self.widget.bind("<Leave>", lambda _: None)
            self.widget.bind("<ButtonPress>", lambda _: None)
        else:
            # Should be 'normal', but any string value is accepted.
            self.widget.bind("<Enter>", self.on_enter)
            self.widget.bind("<Leave>", self.on_leave)
            self.widget.bind("<ButtonPress>", self.close_now)

        self.waiting = None
        self.tt_win = None

    def cancel_wait(self) -> None:
        """
        Cancel *wait_time* to immediately close the tooltip.
        """
        waiting = self.waiting

        # self.waiting is defined in on_enter() as an after() delay.
        self.waiting = None
        if waiting:
            self.widget.after_cancel(waiting)

    def on_enter(self, event=None) -> None:
        """
        Trigger display of the tooltip when cursor rests on the widget.

        :param event: Implicit virtual event of mouse binding.
        :return: The bound event action.
        """
        self.cancel_wait()
        self.waiting = self.widget.after(self.wait_time, self.show_tt)

        return event

    def on_leave(self, event=None) -> None:
        """
        Remove display of the tooltip when cursor leaves the widget.

        :param event: Implicit virtual event of mouse binding.
        :return: The bound event action.
        """
        # On macOS, need to delay destroy() b/c any
        #   mouse movement in the widget causes a re-draw
        #   of the Toplevel tooltip. A delay lessens the annoyance.
        self.cancel_wait()
        if self.tt_win:
            self.tt_win.after(self.wait_time // 2, self.tt_win.destroy)
        self.tt_win = None

        return event

    def close_now(self, event=None) -> None:
        """
        Remove display of the tooltip when widget is clicked.

        :param event: Implicit virtual event of mouse binding.
        :return: The bound event action.
        """
        # This close method, separate from on_leave, is needed on macOS to
        #   close on button click without a ghost tt_win behind parent win.
        self.cancel_wait()
        if self.tt_win:
            self.tt_win.destroy()
        self.tt_win = None

        return event

    @staticmethod
    def tip_pos_calculator(widget: tk,
                           label: tk.Label,
                           tip_delta: tuple = (10, 5)) -> tuple:
        """
        Set screen position of the tooltip Toplevel so that it remains
        on screen with proper padding.

        :param widget: The tk.widget of the tooltip call.
        :param label: The tk.Label to display the *tt_text*.
        :param tip_delta: Pixel (x, y) buffer for "offscreen" toplevel
            position relative to mouse position (default (10, 5)).
        :return: Tuple of pixel (x, y) used to set tooltip geometry().
        """
        wgt = widget

        s_width, s_height = wgt.winfo_screenwidth(), wgt.winfo_screenheight()

        width, height = (label.winfo_reqwidth() + 10,
                         label.winfo_reqheight() + 6)

        mouse_x, mouse_y = wgt.winfo_pointerxy()

        _x1, _y1 = mouse_x + tip_delta[0], mouse_y + tip_delta[1]
        _x2, _y2 = _x1 + width, _y1 + height

        x_delta = _x2 - s_width
        x_delta = max(x_delta, 0)

        y_delta = _y2 - s_height
        y_delta = max(y_delta, 0)

        offscreen = (x_delta, y_delta) != (0, 0)

        if offscreen:

            if x_delta:
                _x1 = mouse_x - tip_delta[0] - width

            if y_delta:
                _y1 = mouse_y - tip_delta[1] - height

        offscreen_again = _y1 < 0  # out on the top

        if offscreen_again:
            # No further checks will be done.
            _y1 = 0

        return _x1, _y1

    def show_tt(self) -> None:
        """
        Create the tooltip as Toplevel. The order of statements is
        optimized for best performance on Linux, Windows, and macOS.
        """

        tt_bg = 'LightYellow1'
        tt_fg = 'gray10'

        # Minimize the window until everything is loaded to prevent
        #   annoying re-draw on some systems.
        # Bring new window to the top to prevent it hiding behind
        #   parent window on some systems.
        self.tt_win = tk.Toplevel(self.widget)
        self.tt_win.overrideredirect(True)
        self.tt_win.wm_withdraw()
        self.tt_win.wm_attributes('-topmost', True)

        tt_frame = tk.Frame(self.tt_win,
                            background=tt_bg,
                            borderwidth=0)
        tt_label = tk.Label(
            tt_frame,
            text=self.tt_text,
            font='TkTooltipFont',
            justify=tk.LEFT,
            background=tt_bg,
            foreground=tt_fg,
            relief=tk.SOLID,
            borderwidth=0,
            wraplength=self.wrap_len)
        tt_frame.grid()
        tt_label.grid(padx=16, pady=16, sticky=tk.NSEW)

        _x, _y = self.tip_pos_calculator(self.widget, tt_label)
        self.tt_win.wm_geometry(f'+{_x}+{_y}')

        self.tt_win.wm_deiconify()

        # With macOS, need to unset wm_overridedredirect() to
        #   fully remove, not just deactivate, the title bar.
        #   https://stackoverflow.com/questions/63613253/
        #   how-to-disable-the-title-bar-in-tkinter-on-a-mac/
        if sys.platform[:3] == 'dar':
            self.tt_win.overrideredirect(False)

        self.tt_win.focus_force()


def beep(repeats: int) -> None:
    """
    Play do_beep sound through the computer's speaker.

    :param repeats: Number of times to repeat the do_beep.
    :return: None
    """

    # Cannot repeat a sleep interval shorter than the sound play duration.
    for _ in range(repeats):
        if 'win' in sys.platform:
            freq = 500
            dur = 200
            winsound.Beep(freq, dur)
        else:
            # Linux/Mac print keyword arguments are needed to not insert newlines.
            # '\N{BEL}' works from terminal, but not from PyCharm 'Run' interpreter.
            print('\N{BEL}', end='', flush=True)
        sleep(0.6)


def enter_only_digits(entry, action_type) -> bool:
    """
    Only digits are accepted and displayed in Entry field.
    Used with register() to configure Entry kw validatecommand. Example:
    myentry.configure(
        validate='key', textvariable=myvalue,
        validatecommand=(myentry.register(enter_only_digits), '%P', '%d')
        )

    :param entry: value entered into an Entry() widget (%P).
    :param action_type: edit action code (%d).
    :return: True or False
    """
    # Need to restrict entries to only digits,
    #   MUST use action type parameter to allow user to delete first number
    #   entered when wants to re-enter following backspace deletion.
    # source: https://stackoverflow.com/questions/4140437/
    # %P = value of the entry if the edit is allowed
    # Desired action type 1 is "insert", %d.
    if action_type == '1' and not entry.isdigit():
        return False

    return True


def position_wrt_window(window: tk.Tk,
                        offset_x: int = 30,
                        offset_y: int = 20) -> str:
    """
    Get screen position of a tkinter object and apply optional
    coordinate offsets. Used to set screen position of a child Toplevel
    with respect to the parent window, but can be used for any widget.
    Example use with the geometry() method:
      mytopwin.geometry(utils.position_wrt_window(root, 15, -15))

    Args:
        window: The tk object (e.g., 'root', 'app', '.!toplevel2')
            of mainloop for which to get its screen pixel coordinates.
        offset_x: optional pixels to add/subtract to x coordinate of
            *window*.
        offset_y: optional pixels to add/subtract to y coordinate of
            *window*.
    Returns: x and y screen pixel coordinates as string, f'+{x}+{y}'
    """
    coord_x = window.winfo_x() + offset_x
    coord_y = window.winfo_y() + offset_y

    return f'+{coord_x}+{coord_y}'


def quit_gui(mainloop: tk.Tk, keybind=None) -> None:
    """
    Error-free and informative exit from the program.
    Called from multiple widgets or keybindings.

    :param mainloop: The main tk.Tk() window running in the mainloop.
    :param keybind: Implicit event passed from bind().
    """

    # Write exit message to an existing log file, even if the setting
    #   "log to file" was not selected, BUT not for additional instances.
    time_now = datetime.now().strftime(const.LONG_FMT)
    quit_txt = f'\n{time_now}; *** User quit the program. ***\n'
    print(quit_txt)

    if Path.exists(Logs.LOGFILE):
        files.append_txt(dest=Logs.LOGFILE,
                         savetxt=quit_txt,
                         showmsg=False)

    matplotlib.pyplot.close('all')
    mainloop.update_idletasks()
    mainloop.after(200)
    mainloop.destroy()

    return keybind


def exit_text() -> str:
    """Return a string to be used in the exit message."""
    text = (f'\nNOTICE: {instances.program_name()} is already running from'
            f' {Path.cwd()}. Exiting...\n')

    if getattr(sys, 'frozen', False):  # Is PyInstaller stand-alone app.
        text = f'\nNOTICE: {instances.program_name()} is already running. Exiting...\n'

    return text


def verify(text: str) -> int:
    """
    Generate a custom hash value for the input string. Intended for
    verification of Project distribution file content.
    Code source:
    https://stackoverflow.com/questions/27522626/
    hash-function-in-python-3-3-returns-different-results-between-sessions/70262376#70262376

    :param text: A string object.
    :return: An identical hash integer for identical *text* objects.
    """
    my_hash = 0
    for char in text:
        my_hash = (my_hash * 281 ^ ord(char) * 997) & 0xFFFFFFFF
    return my_hash
