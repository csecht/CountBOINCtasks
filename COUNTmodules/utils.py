#!/usr/bin/env python3
"""
General utility functions in gcount-tasks.
Functions:
    absolute_path_to() - Get absolute path to files and directories.
    position_wrt_window() - Set coordinates of a tk.Toplevel relative
        to another window position.
    get_toplevel - Identify the parent tk.Toplevel with focus.
    enter_only_digits() - Constrain tk.Entry() values to digits.

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
__module_name__ = 'utils.py'
__module_ver__ = '0.1.9'
__dev_environment__ = "Python 3.8 - 3.9"
__project_url__ = 'https://github.com/csecht/CountBOINCtasks'
__maintainer__ = 'cecht'
__status__ = 'Development Status :: 4 - Beta'

import sys
import tkinter as tk
from pathlib import Path


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
        self.tt_bg = 'LightYellow1'

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

    def on_enter(self, event=None):
        """
        Trigger display of the tooltip when cursor rests on the widget.

        :param event: Implicit virtual event of mouse binding.
        :return: The bound event action.
        """
        self.cancel_wait()
        self.waiting = self.widget.after(self.wait_time, self.show_tt)

        return event

    def on_leave(self, event=None):
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

    def close_now(self, event=None):
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
                           tip_delta=(10, 5)) -> tuple:
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
        # Minimize the window until everything is loaded to prevent
        #   annoying re-draw on some systems.
        # Bring new window to the top to prevent it hiding behind
        #   parent window on some systems.
        self.tt_win = tk.Toplevel(self.widget)
        self.tt_win.overrideredirect(True)
        self.tt_win.wm_withdraw()
        self.tt_win.wm_attributes('-topmost', True)

        tt_frame = tk.Frame(self.tt_win,
                            background=self.tt_bg,
                            borderwidth=0)
        tt_label = tk.Label(
            tt_frame,
            text=self.tt_text,
            font='TkTooltipFont',
            justify=tk.LEFT,
            background=self.tt_bg,
            relief=tk.SOLID,
            borderwidth=0,
            wraplength=self.wrap_len)
        tt_frame.grid()
        tt_label.grid(padx=10, pady=6, sticky=tk.NSEW)

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


def absolute_path_to(relative_path: str) -> Path:
    """
    Get absolute path to files and directories.
    A temporary folder, _MEIPASS var, is used by -onefile or --windowed
    distributions from PyInstaller, e.g. for an 'images' directory.
    Python execution from Terminal will use the parent folder if a file
    name is given as the *relative_path*.

    :param relative_path: File or dir name path, as string.
    :return: Absolute path as pathlib Path object.
    """
    # Modified from: https://stackoverflow.com/questions/7674790/
    #    bundling-data-files-with -pyinstaller-onefile and PyInstaller manual.
    if getattr(sys, 'frozen', False):  # hasattr(sys, '_MEIPASS'):
        base_path = getattr(sys, '_MEIPASS', Path(Path(__file__).resolve()).parent)

        return Path(base_path) / relative_path

    return Path(relative_path).resolve()


def position_wrt_window(window, offset_x=0, offset_y=0) -> str:
    """
    Get screen position of a tkinter Toplevel object and apply optional
    coordinate offsets. Used to set screen position of a child Toplevel
    with respect to the parent window.
    Example use with the geometry() method:
      mytopwin.geometry(utils.position_wrt_window(root, 15, -15))
    When used with get_toplevel(), it is expected that all the parent's
    Toplevel Button() widgets are configured for 'takefocus=False'.

    :param window: The tk window object (e.g., 'root', 'app',
                   '.!toplevel2') of mainloop for which to get its
                   screen pixel coordinates.
    :param offset_x: optional pixels to add/subtract to x coordinate of
                     *window*.
    :param offset_y: optional pixels to add/subtract to x coordinate of
                     *window*.
    :return: x and y screen pixel coordinates as string, f'+{x}+{y}'
    """
    coord_x = window.winfo_x() + offset_x
    coord_y = window.winfo_y() + offset_y

    return f'+{coord_x}+{coord_y}'


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
