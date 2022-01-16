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
__module_ver__ = '0.1.4'
__dev_environment__ = "Python 3.8 - 3.9"
__project_url__ = 'https://github.com/csecht/CountBOINCtasks'
__maintainer__ = 'cecht'
__status__ = 'Development Status :: 4 - Beta'

import sys
import tkinter as tk
from pathlib import Path
from typing import Union, Any

MY_OS = sys.platform[:3]


class Tooltip:
    """
    Bind mouse hover events to create a Toplevel tooltip with the given
    text for the given widget.

    USAGE: Tooltip(tk.widget, text, wait_time, wrap_length)
        widget for which the toottip is to appear,
        text string of the tip,
        wait_time (ms) delay of tip appearance (optional: default is set),
        wrap_length (pixels) of tip window width (optional: default is set).

        Tooltip mouse event bindings are persistent. Can deactivate a
        tooltip with widget.unbind() for the mouse events Enter, Leave,
        AND ButtonPress.

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

    - Customized for CountBOINCtasks Project
        by Craig Echt, 12 January 2022.
        Tested on Linux Ubuntu 20.04, Windows 10, macOS 10.13,
        running Python 3.8 - 3.9
    """

    def __init__(self, widget: tk, tt_text: str, wait_time=500, wrap_len=250):

        # wait_time is milliseconds, wrap_len is pixels.
        self.widget = widget
        self.tt_text = tt_text
        self.wait_time = wait_time
        self.wrap_len = wrap_len
        self.bg = 'LightYellow1'

        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
        self.widget.bind("<ButtonPress>", self.on_leave)
        self.id = None
        self.tt_win = None

    def on_enter(self, event=None) -> None:
        """
        Trigger display of the tooltip when cursor rests on the widget.

        :param event: Implicit virtual event of mouse binding.
        """
        self.tip_close()
        self.id = self.widget.after(self.wait_time, self.show)

    def on_leave(self, event=None) -> None:
        """
        Remove display of the tooltip when cursor leaves the widget.

        :param event: Implicit virtual event of mouse binding.
        """
        # On macOS, need to delay the destroy() b/c any
        #   mouse movement in the widget causes a re-draw
        #   of the tooltip. A delay lessens the annoyance.
        self.tip_close()
        if self.tt_win:
            self.tt_win.after(self.wait_time // 2, self.tt_win.destroy)
        self.tt_win = None

    def tip_close(self) -> None:
        """
        Immediately cancel on_enter() wait_time to close the tooltip.
        """
        id_ = self.id
        self.id = None
        if id_:
            self.widget.after_cancel(id_)

    @staticmethod
    def tip_pos_calculator(widget, label, tip_delta=(10, 5)) -> tuple:
        """
        Set screen position of the tooltip Toplevel so that it remains
        on screen with proper padding.

        :param widget: the tk.widget from the call
        :param label: The tk.Label to display the tt_text.
        :param tip_delta: Pixel (x, y) buffer to consider "off-screen"
            relative to mouse position.
        :return: Tuple of pixel (x, y) used to set tooltip geometry().
        """
        w = widget

        s_width, s_height = w.winfo_screenwidth(), w.winfo_screenheight()

        width, height = (label.winfo_reqwidth() + 10,
                         label.winfo_reqheight() + 6)

        mouse_x, mouse_y = w.winfo_pointerxy()

        x1, y1 = mouse_x + tip_delta[0], mouse_y + tip_delta[1]
        x2, y2 = x1 + width, y1 + height

        x_delta = x2 - s_width
        if x_delta < 0:
            x_delta = 0
        y_delta = y2 - s_height
        if y_delta < 0:
            y_delta = 0

        offscreen = (x_delta, y_delta) != (0, 0)

        if offscreen:

            if x_delta:
                x1 = mouse_x - tip_delta[0] - width

            if y_delta:
                y1 = mouse_y - tip_delta[1] - height

        offscreen_again = y1 < 0  # out on the top

        if offscreen_again:
            # No further checks will be done.
            y1 = 0

        return x1, y1

    def show(self) -> None:
        """
        Create the tooltip Toplevel. The order of statements is
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
        win = tk.Frame(self.tt_win,
                       background=self.bg,
                       borderwidth=0)
        label = tk.Label(
            win,
            text=self.tt_text,
            font='TkTooltipFont',
            justify=tk.LEFT,
            background=self.bg,
            relief=tk.SOLID,
            borderwidth=0,
            wraplength=self.wrap_len)
        win.grid()
        label.grid(padx=10, pady=6, sticky=tk.NSEW)

        x, y = self.tip_pos_calculator(self.widget, label)

        self.tt_win.wm_geometry(f'+{x}+{y}')

        self.tt_win.wm_deiconify()

        # With macOS, need to unset wm_overridedredirect() to
        #   fully remove, not just deactivate, the title bar.
        #   https://stackoverflow.com/questions/63613253/
        #   how-to-disable-the-title-bar-in-tkinter-on-a-mac/
        if MY_OS == 'dar':
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

    :param window: The main window object (e.g., 'root', 'app',
                   '.!toplevel2') of the tk() mainloop for which to get
                   its screen pixel coordinates.
    :param offset_x: optional pixels to add/subtract to x coordinate of
                     *window*.
    :param offset_y: optional pixels to add/subtract to x coordinate of
                     *window*.
    :return: x and y screen pixel coordinates as string, f'+{x}+{y}'
    """
    coord_x = window.winfo_x() + offset_x
    coord_y = window.winfo_y() + offset_y
    return f'+{coord_x}+{coord_y}'


def get_toplevel(action: str, mainwin) -> Union[str, Any]:
    """
    Identify the parent tkinter.Toplevel() window when it, or its
    child widget, has focus.
    Works as intended when Button widgets in parent toplevel or
    *mainwin* do not retain focus, i.e., 'takefocus=False'.

    :param action: The action needed for the parent; e.g.,
                   'position', 'winpath'.
    :param mainwin: The main window object of the tk() mainloop, e.g.,
                    'root', 'main', or 'app', etc.
    :return: For *action* 'position', returns string of screen
             coordinates for the parent toplevel window.
             For *action* 'winpath', returns the tk window path
             name for the parent toplevel window.
    """
    # Based on https://stackoverflow.com/questions/66384144/
    # Need to cover all cases when the focus is on any toplevel window,
    #  or on a child of that window path, i.e. '.!text' or '.!frame'.
    # There may be many children in *mainwin* and any target toplevel
    #   window will likely be listed at or toward the end, so read
    #   children list in reverse.
    if action == 'position':
        coordinates = None
        for child in reversed(mainwin.winfo_children()):
            if child == child.focus_get():
                coordinates = position_wrt_window(child, 30, 20)
            elif '.!text' in str(child.focus_get()):
                parent = str(child.focus_get())[:-6]
                if parent in str(child):
                    coordinates = position_wrt_window(child, 30, 20)
            elif '.!frame' in str(child.focus_get()):
                parent = str(child.focus_get())[:-7]
                if parent in str(child):
                    coordinates = position_wrt_window(child, 30, 20)
            elif str(child.focus_get()) == '.':
                coordinates =  position_wrt_window(mainwin, 30, 20)
        return coordinates
    if action == 'winpath':
        relative_path = mainwin.winfo_children()[-1]
        for child in reversed(mainwin.winfo_children()):
            if child == child.focus_get():
                relative_path = child
            elif '.!text' in str(child.focus_get()):
                parent = str(child.focus_get())[:-6]
                if parent in str(child):
                    relative_path = child
            elif '.!frame' in str(child.focus_get()):
                parent = str(child.focus_get())[:-7]
                if parent in str(child):
                    relative_path = child
            elif str(child.focus_get()) == '.':
                relative_path = mainwin
        return relative_path
    return None


def enter_only_digits(entry_string, action_type) -> bool:
    """
    Only digits are accepted and displayed in Entry field.
    Used with register() to configure Entry kw validatecommand. Example:
    myentry.configure(
        validate='key', textvariable=myvalue,
        validatecommand=(myentry.register(enter_only_digits), '%P', '%d')
        )

    :param entry_string: value entered into an Entry() widget (%P).
    :param action_type: edit action code (%d).
    :return: True or False
    """
    # Need to restrict entries to only digits,
    #   MUST use action type parameter to allow user to delete first number
    #   entered when wants to re-enter following backspace deletion.
    # source: https://stackoverflow.com/questions/4140437/
    # %P = value of the entry if the edit is allowed
    # Desired action type 1 is "insert", %d.
    if action_type == '1' and not entry_string.isdigit():
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
