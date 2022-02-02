#!/usr/bin/env python3
"""
Functions to set tkinter mouse click and keyboard bindings.
Functions:
    click() - Mouse button bindings for a named object.
    keyboard() - Bind a key to a function for the specified toplevel.

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
__module_name__ = 'binds.py'
__module_ver__ = '0.1.8'
__dev_environment__ = "Python 3.8 - 3.9"
__project_url__ = 'https://github.com/csecht/CountBOINCtasks'
__maintainer__ = 'cecht'
__status__ = 'Development Status :: 4 - Beta'

from sys import platform, exit as sysexit
from tkinter import constants, Menu

from COUNTmodules import files, utils

MY_OS = platform[:3]


def click(click_type, click_widget, mainwin) -> None:
    """
    Mouse button bindings for the named tk widget.
    Creates pop-up menu of commands for the clicked object.
    Example: from COUNTmodules import binds
             binds.click('right', mywidget, root)

    :param click_type: Example mouse button or button modifiers;
        left', 'right', 'shift', 'ctrl', 'shiftctrl', etc.
        'right': popup menu of text edit and window commands.
    :param click_widget: Name of the widget in which click commands are
        to be active.
    :param mainwin: The main window of the tk() mainloop, e.g.,
        'root', 'main', 'app', etc., from which to identify its
        tk.Toplevel child that has focus.
    """

    def on_click(event, command):
        """
        Sets menu command to the selected predefined virtual event.
        Event is a unifying binding across multiple platforms.
        https://www.tcl.tk/man/tcl8.6/TkCmd/event.htm#M7
        """
        # Need to set possible Text widgets to be editable in case
        #   they are set to be readonly, tk.DISABLED.
        event.widget.event_generate(f'<<{command}>>')

    # Based on: https://stackoverflow.com/questions/57701023/
    def popup_menu(event):
        popup = Menu(None, tearoff=0, takefocus=0)

        popup.add_command(
            label='Select all',
            command=lambda: on_click(event, 'SelectAll'))
        popup.add_command(
            label='Copy',
            command=lambda: on_click(event, 'Copy'))
        popup.add_command(
            label='Paste',
            command=lambda: on_click(event, 'Paste'))
        popup.add_command(
            label='Cut',
            command=lambda: on_click(event, 'Cut'))
        popup.add(constants.SEPARATOR)
        popup.add_command(
            label='Close window',
            command=lambda: utils.get_toplevel('winpath', mainwin).destroy())

        popup.tk_popup(event.x_root + 10, event.y_root + 15)

    if click_type == 'right':
        if MY_OS in 'lin, win':
            click_widget.bind('<Button-3>', popup_menu)
        elif MY_OS == 'dar':
            click_widget.bind('<Button-2>', popup_menu)


def keyboard(func: str, toplevel,
             mainloop=None, filepath=None, text=None) -> None:
    """
    Bind a key to a function for the specified Toplevel() window. Use to
    add standard keyboard actions or to provide keybinding equivalents
    for button commands used in the Toplevel() window.

    Example usage in a function that creates a mytopwin Toplevel and
    using import: 'from COUNTmodules import binds':
        binds.keyboard('close', mytopwin)
        binds.keyboard('append', mytopwin, MYFILEPATH, txt)

    :param func: Function to execute: 'close', 'append', 'saveas'.
                 For 'close', the key is 'w' with OS-specific modifier.
                 For 'append' and 'saveas', the key is 's' with
                 OS-specific modifier.
    :param toplevel: Name of tk.Toplevel() window object.
    :param mainloop: The tk() mainloop object ('root', 'main', etc.);
                use with the *func* 'close' option.
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
        toplevel.bind(
            f'<{f"{cmd_key}"}-w>',
            lambda _: utils.get_toplevel('winpath', mainloop).destroy())

    if func == 'append':
        toplevel.bind(f'<{f"{cmd_key}"}-s>',
                      lambda _: files.append_txt(filepath, text, True, toplevel))

    if func == 'saveas':
        toplevel.bind(f'<{f"{cmd_key}"}-s>',
                      lambda _: files.save_as(filepath, toplevel))


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
    sysexit(0)


if __name__ == '__main__':
    about()
