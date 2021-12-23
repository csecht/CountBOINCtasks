#!/usr/bin/env python3
"""
Functions to set click and key bindings

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
__program_name__ = 'gcount-tasks, count-tasks'
__version__ = '0.0.1'
__dev_environment__ = "Python 3.8 - 3.9"
__project_url__ = 'https://github.com/csecht/CountBOINCtasks'
__maintainer__ = 'cecht'
__status__ = 'Development Status :: 4 - Beta'

import sys
import tkinter as tk
from COUNTmodules import files

MY_OS = sys.platform[:3]


# This is called only internally
def close_toplevel(widget, keybind=None) -> None:
    """
    Close the toplevel window that has focus.
    Use with keybinding or right-click pop-up commands.

    :param widget: The widget (usually the 'root', 'main', or 'app'
                   object) on which to get the focus on and destroy().
    :param keybind: Empty parameter to pass implicit keybinding event.
    """
    # Based on https://stackoverflow.com/questions/66384144/
    # Need to cover all cases when the focus is on any toplevel window,
    #  or on a child of that window, i.e. .!text or .!frame.
    # There may be many children in *widget* and any toplevel window will
    #   be listed at or toward the end, so read children list in reverse.
    # To prevent all toplevels from closing, stop when the focus
    #   toplevel parent is found.

    for widget in reversed(widget.winfo_children()):
        # pylint: disable=no-else-break
        if widget == widget.focus_get():
            widget.destroy()
            return keybind
        if '.!text' in str(widget.focus_get()):
            parent = str(widget.focus_get())[:-6]
            if parent in str(widget):
                widget.destroy()
                return keybind
        if '.!frame' in str(widget.focus_get()):
            parent = str(widget.focus_get())[:-7]
            if parent in str(widget):
                widget.destroy()
                return keybind
    return keybind


def click(widget, click_obj, click_type) -> None:
    """
    Mouse button bindings for the named object.
    Creates pop-up menu of commands for the clicked object.

    :param widget: The widget (usually the 'root', 'main', or 'app'
                   object) to pass to close_toplevel().
    :param click_obj: Name of the object in which click commands are
                      to be active.
    :param click_type: Example mouse button or button modifiers;
                     'left', 'right', 'shift', 'ctrl', 'shiftctrl', etc.
    """

    def on_click(event, command):
        """
        Sets menu command to the selected predefined virtual event.
        Event is a unifying binding across multiple platforms.
        https://www.tcl.tk/man/tcl8.6/TkCmd/event.htm#M7
        """
        # Need to set possible Text widgets to be editable in case
        #   they are set to be readonly, tk.DISABLED.
        click_obj.configure(state=tk.NORMAL)
        event.widget.event_generate(f'<<{command}>>')

    # Based on: https://stackoverflow.com/questions/57701023/
    def popup_menu(event):
        right_click_menu = tk.Menu(None, tearoff=0, takefocus=0)

        right_click_menu.add_command(
            label='Select all',
            command=lambda: on_click(event, 'SelectAll'))
        right_click_menu.add_command(
            label='Copy',
            command=lambda: on_click(event, 'Copy'))
        right_click_menu.add_command(
            label='Paste',
            command=lambda: on_click(event, 'Paste'))
        right_click_menu.add_command(
            label='Cut',
            command=lambda: on_click(event, 'Cut'))
        right_click_menu.add(tk.SEPARATOR)
        right_click_menu.add_command(label='Close window',
                                     command=lambda: close_toplevel(widget))

        right_click_menu.tk_popup(event.x_root + 10, event.y_root + 15)

    if click_type == 'right':
        if MY_OS in 'lin, win':
            click_obj.bind('<Button-3>', popup_menu)
        elif MY_OS == 'dar':
            click_obj.bind('<Button-2>', popup_menu)


def keyboard(widget, toplevel, func: str, filepath=None, text=None) -> None:
    """
    Bind a key to a function for the specified Toplevel() window. Use to
    add standard keyboard actions or to provide keybinding equivalents
    for button commands used in the Toplevel() window.

    Example usage in a function that creates mytopwin:
    keyboard(mytopwin, 'close'), Mod-w will close mytopwin.
    keyboard(mytopwin, 'append', MYFILEPATH, txt), Mod-s will
    append txt string to the file MYFILEPATH.

    :param widget: The widget (usually the 'root', 'main', or 'app'
                   object) to pass to close_toplevel().
    :param toplevel: Name of tk.Toplevel() object.
    :param func: Function to execute: 'close', 'append', 'saveas'.
                 For 'close', the key is 'w' with OS-specific modifier.
                 For 'append' and 'saveas', the key is 's' with
                 OS-specific modifier.
    :param filepath: A Path file object; use with *func* 'saveas' and
                     'append'.
    :param text: Text to append to *filepath*; use with *func* 'append'.
    """
    cmd_key = ''
    if MY_OS in 'lin, win':
        cmd_key = 'Control'
    elif MY_OS == 'dar':
        cmd_key = 'Command'

    if func == 'close':
        toplevel.bind(f'<{f"{cmd_key}"}-w>', lambda _: close_toplevel(widget))

    if func == 'append':
        toplevel.bind(f'<{f"{cmd_key}"}-s>',
                      lambda _: files.append_txt(filepath, text, True))

    if func == 'saveas':
        toplevel.bind(f'<{f"{cmd_key}"}-s>',
                      lambda _: files.save_as(filepath))


def about() -> None:
    """
    Print details about_gui this module.
    """
    print(__doc__)
    print(f'{"Author:".ljust(11)}', __author__)
    print(f'{"Copyright:".ljust(11)}', __copyright__)
    print(f'{"License:".ljust(11)}', __license__)
    print(f'{"Module:".ljust(11)}', __program_name__)
    print(f'{"Version:".ljust(11)}', __version__)
    print(f'{"Dev Env:".ljust(11)}', __dev_environment__)
    print(f'{"URL:".ljust(11)}', __project_url__)
    print(f'{"Maintainer:".ljust(11)}',  __maintainer__)
    print(f'{"Status:".ljust(11)}', __status__)
    sys.exit(0)


if __name__ == '__main__':
    about()
